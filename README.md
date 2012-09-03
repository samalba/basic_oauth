Basic oauth
===========

What is it?
-----------

The Oauth v2 spec defines several authorization grant. This library implements
the "Resource Owner Password Credentials Grant" as described in
<http://tools.ietf.org/html/draft-ietf-oauth-v2-31#section-4.3>

Requirements:

    * [Flask](http://flask.pocoo.org/)
    * [Redis](http://redis.io/)

Why using it?
-------------

The goal of this Grant is to replace the classic "HTTP Basic over SSL" widely
used. With Oauth, you exchange your crendentials against a token.

This mechanism has several advantages:

    * The client does not pass the full credentials for each request.
    * The server does not check the username and password each time, it will 
    only check the access token, this will reduce the database lookups.

Basic Oauth uses Redis to store the sessions.

Is it secure?
-------------

__It would be stupid to use this mechanism without SSL__. Even if the token is
passed instead of the credentials, the credentials needs to be passed in clear
text during the Authentication phase. Also, it can be problematic to lose the
token.

To limit the risk of losing the token, every single token generated is signed
using the User-Agent and the client IP address. If an attacker tries to re-use
a stolen token, he will have to connect to the same IP and using the same
User-Agent (browser version, OS, architecture) to get access. A wrong try will
result in destroying the session.