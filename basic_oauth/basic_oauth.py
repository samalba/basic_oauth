
""" This module implements the Resource Owner Password Credentials Grant
as described in: http://tools.ietf.org/html/draft-ietf-oauth-v2-31#section-4.3
"""

import os
import functools
import hashlib
import base64

import flask
import redis


def response(obj, code=200, redirect_uri=None, cookies=None):
    headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache'
            }
    response = flask.make_response(flask.json.dumps(obj, indent=4), code, headers)
    if cookies:
        for cookie in cookies:
            response.set_cookie(**cookie)
    return response

def error_response(reason, description=None):
    obj = {
        'error': reason
        }
    if description:
        obj['error_description'] = description
    return response(obj, 400)

def get_client_ip(environ):
    try:
        return environ['HTTP_X_FORWARDED_FOR'].split(',').pop().strip()
    except KeyError:
        return environ['REMOTE_ADDR']

def sign_token(token, remote_addr, user_agent):
    sha = hashlib.sha1()
    sha.update('{0}:{1}:{2}'.format(token, remote_addr, user_agent))
    return sha.hexdigest()


class BasicOauth(object):

    def __init__(self, flask_app, allow_origin=None, redis_config=None, token_ttl=3600):
        self._flask_app = flask_app
        # Simple in-ram credentials db
        self.credentials = []
        # Auth handler to abstract db calls
        # can be set in order to use a real database
        self.authenticate_handler = None
        # In secure mode, the cookie will have the secure attribute be set only
        # for https connections
        self.secure = True
        self._token_ttl = token_ttl
        # Redis connection
        redis_config = redis_config or {}
        self._redis = redis.StrictRedis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0))

    def authenticate(self, username, password):
        """ Authenticate a user and returns the user id """
        if self.authenticate_handler is not None:
            return self.authenticate_handler(username, password)
        creds = (username, password)
        if creds in self.credentials:
            return self.credentials.index(creds)

    def mount_endpoint(self, name, uri):
        endpoints = {
                'login': {
                    'rule': uri,
                    'endpoint': 'oauth_login_endpoint',
                    'view_func': self.login_endpoint,
                    'methods': ['POST']
                    },
                'logout': {
                    'rule': uri,
                    'endpoint': 'oauth_logout_endpoint',
                    'view_func': self.logout_endpoint,
                    'methods': ['GET']
                    },
                'script': {
                    'rule': uri,
                    'endpoint': 'oauth_script_endpoint',
                    'view_func': self.script_endpoint,
                    'methods': ['GET']
                    }
                }
        if name not in endpoints:
            raise ValueError('No such mount type')
        self._flask_app.add_url_rule(**endpoints[name])

    def login_endpoint(self):
        """ Login endpoint which receives credentials in clear text """
        req = flask.request
        grant_type = req.form.get('grant_type')
        username = req.form.get('username')
        password = req.form.get('password')
        if not grant_type or not username or not password:
            return error_response('invalid_request')
        if grant_type != 'password':
            return error_response('unsupported_grant_type')
        user_id = self.authenticate(username, password)
        if user_id is None:
            return error_response('invalid_grant')
        access_token = base64.urlsafe_b64encode(os.urandom(32))
        # Create a new session in Redis
        token_key = 'token:' + access_token
        remote_addr = get_client_ip(req.environ)
        user_agent = req.environ.get('HTTP_USER_AGENT', '')
        token_signature = sign_token(access_token, remote_addr, user_agent)
        self._redis.rpush(token_key, token_signature)
        self._redis.rpush(token_key, user_id)
        self._redis.rpush(token_key, remote_addr)
        self._redis.rpush(token_key, user_agent)
        self._redis.expire(token_key, self._token_ttl)
        cookie = {
                'key': 'access_token',
                'value': access_token,
                'max_age': self._token_ttl,
                'secure': self.secure
                }
        return response({
            'access_token': access_token,
            'token_type': 'bearer',
            'expires_in': self._token_ttl
            }, cookies=[cookie])

    def logout_endpoint(self):
        """ Logout """
        req = flask.request
        access_token = req.args.get('access_token') or \
                req.cookies.get('access_token')
        if not access_token:
            return response({})
        token_key = 'token:' + access_token
        self._redis.delete(token_key)
        return response({})

    def require(self, f):
        """ Decorator that authorizes an access token """
        @functools.wraps(f)
        def wrapper(*args, **kwds):
            req = flask.request
            # Token can be passed through an uri argument or from a cookie
            access_token = req.args.get('access_token') or \
                    req.cookies.get('access_token')
            if not access_token:
                return error_response('invalid_request')
            token_key = 'token:' + access_token
            data = self._redis.lrange(token_key, 0, 1)
            if not data or len(data) != 2:
                return error_response('invalid_grant')
            token_signature = sign_token(
                    access_token,
                    get_client_ip(req.environ),
                    req.environ.get('HTTP_USER_AGENT', ''))
            if token_signature != data[0]:
                # The signature is wrong (the access token is sent from a
                # different IP or with a different User-Agent), destroying
                # the session for safety
                self._redis.delete(token_key)
                return error_response('invalid_grant')
            # Refresh the token TTL
            self._redis.expire(token_key, self._token_ttl)
            # Pass the user_id as first argument
            return f(int(data[1]), *args, **kwds)
        return wrapper

    def script_endpoint(self):
        script_path = os.path.join(
                os.path.dirname(__file__),
                'oauth_client.js')
        return flask.send_file(script_path)
