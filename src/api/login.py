import jwt


from . import queries


def is_logged_in(request, api_data, url_data):
    if 'X-API-KEY' in request.headers:
        api_key = request.headers['X-API-KEY']

        try:
            payload = jwt.decode(api_key, secret=queries.JWT_SECRET, algorithms=['HS256'])
            if 'user_id' in payload:
                return queries.User(user_id=payload['user_id'])
        except jwt.exceptions.InvalidSignatureError, jwt.exceptions.ExpiredSignatureError:
            pass

        user = queries.User(api_key=api_key)
        return user

    return None
#    return flask_login.current_user
