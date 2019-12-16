import jwt
import logging
from flask import request

from . import queries

logger = logging.getLogger(__name__)


def is_logged_in(request, api_data, url_data):
    api_data = api_data or {}
    token = api_data.get('url_token') or url_data.get('url_token')
    if token:
        try:
            payload = jwt.decode(token, queries.JWT_SECRET, verify=True)
            if 'user_id' in payload:
                return queries.User(user_id=payload['user_id'], is_authenticated=True)
        except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.ExpiredSignatureError, jwt.exceptions.DecodeError) as e:
            logger.warn("token... %r", e)
            pass

    if 'X-API-KEY' in request.headers:
        api_key = request.headers['X-API-KEY']

        try:
            payload = jwt.decode(api_key, queries.JWT_SECRET, verify=True)
            # logger.warn("payload = %r", payload)
            if 'user_id' in payload:
                return queries.User(user_id=payload['user_id'], is_authenticated=True)
        except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.ExpiredSignatureError, jwt.exceptions.DecodeError) as e:
            pass

        user = queries.User(api_key=api_key)
        if user.is_authenticated:
            request.is_logged_in = True
        return user

    return None
#    return flask_login.current_user
