from .utils import Api, api_register
from .. import auth0

@api_register(None)
class AuthApi(Api):
    def login(self, username=None, password=None):
        resp = auth0.login(username, password)
        return {'key': resp}

    def logout(self, _user=None):
        return auth0.logout(_user.token)

    @Api.config(require_login=True)
    def profile(self, _user=None):
        return _user.profile
