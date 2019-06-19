import logging

from lib.api_framework import api_register, Api


logger = logging.getLogger(__name__)


@api_register(None, require_login=False)
class PCBApi(Api):
    @classmethod
    @Api.config(file_keys=['file'])
    def index(cls, file=None):
        logger.warn("file = %r", file)
        return "hi"
