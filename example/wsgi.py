#!/usr/bin/env python
# http://tools.ietf.org/html/draft-ietf-oauth-v2-31#section-4.3

import flask
import basic_oauth


app = flask.Flask(__name__)

oauth = basic_oauth.BasicOauth(app)
oauth.mount_endpoint('login', '/login')
oauth.mount_endpoint('script', '/js/oauth_client.js')
oauth.credentials.append(('johndoe', 'foobar42'))

@app.route('/')
@oauth.require
def hello(user_id):
    return 'Hello World!'


if __name__ == '__main__':
    app.debug = True
    app.run()
