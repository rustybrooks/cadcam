def is_logged_in(request, api_data, url_data):
    if 'X-API-KEY' in request.headers:
        user = queries.User(api_key=request.headers['X-API-KEY'])
        return user

    return None
#    return flask_login.current_user
