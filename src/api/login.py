import jwt
import logging


from . import queries

logger = logging.getLogger(__name__)


def is_logged_in(request, api_data, url_data):
    if 'X-API-KEY' in request.headers:
        api_key = request.headers['X-API-KEY']
        logger.warn("%r - %r", api_key, queries.JWT_SECRET)

        try:
            payload = jwt.decode(api_key, secret=queries.JWT_SECRET, verify=False)
            logger.warn("payload = %r", payload)
            if 'user_id' in payload:
                return queries.User(user_id=payload['user_id'], is_authenticated=True)
        except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.ExpiredSignatureError, jwt.exceptions.DecodeError) as e:
            logger.warn("%r", e)

        user = queries.User(api_key=api_key)
        return user

    return None
#    return flask_login.current_user
