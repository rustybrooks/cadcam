from lib.api_framework import api_register, Api


@api_register(None, require_login=False)
class PCBApi(Api):
    @classmethod
    def index(cls):
        return "hi"
