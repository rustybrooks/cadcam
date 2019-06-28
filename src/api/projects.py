import logging

from lib.api_framework import api_register, Api

from . import login, queries

logger = logging.getLogger(__name__)


@api_register(None, require_login=login.is_logged_in)
class ProjectsApi(Api):
    @classmethod
    def index(cls, page=1, limit=10, _user=None):
        return {
            'results': queries.projects(user_id=_user.user_id, page=page, limit=limit),
        }

    @classmethod
    def create(cls, project_key=None, project_type='pcb', name=None, _user=None):
        project = queries.project(user_id=_user.user_id, project_key=project_key)
        if project:
            raise cls.BadRequest("Project key '{}' already exists".format(project_key))

        queries.add_project(user_id=_user.user_id, project_key=project_key, name=name, project_type=project_type)

        return {'status': 'ok'}
