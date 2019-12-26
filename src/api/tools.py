import logging

from lib.api_framework import api_register, Api

from . import queries

logger = logging.getLogger(__name__)


@api_register(None, require_login=True)
class ToolsApi(Api):
    @classmethod
    @Api.config(require_login=False)
    def index(cls, page=1, limit=10, sort='tool_key', _user=None):
        return queries.tools(
            user_id=None, page=page, limit=limit, sort=sort
        ) + queries.tools(
            user_id=_user.user_id, page=page, limit=limit, sort=sort
        )
