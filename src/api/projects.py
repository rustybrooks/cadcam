import boto3
import datetime
import io
import logging
import os
import zipfile

from lib.api_framework import api_register, Api
from lib import config

from . import login, queries

logger = logging.getLogger(__name__)

s3 = boto3.client(
    's3',
    aws_access_key_id=config.get_config_key('aws_access_key_id'),
    aws_secret_access_key=config.get_config_key('aws_secret_access_key')
)


@api_register(None, require_login=login.is_logged_in)
class ProjectsApi(Api):
    @classmethod
    def index(cls, page=1, limit=10, _user=None):
        out = {
            'results': queries.projects(user_id=_user.user_id, page=page, limit=limit),
        }

        for r in out['results']:
            r.update({
                'created_ago': (datetime.datetime.utcnow() - r.date_created).total_seconds(),
                'modified_ago': (datetime.datetime.utcnow() - r.date_modified).total_seconds(),
            })

        return out

    @classmethod
    def create(cls, project_key=None, project_type='pcb', name=None, _user=None):
        project = queries.project(user_id=_user.user_id, project_key=project_key)
        if project:
            raise cls.BadRequest("Project key '{}' already exists".format(project_key))

        queries.add_project(user_id=_user.user_id, project_key=project_key, name=name, project_type=project_type)

        return {'status': 'ok'}

    @classmethod
    @Api.config(file_keys=['file'])
    def upload_file(cls, project_key=None, file=None, _user=None):
        logger.warn("project_key=%r, file=%r, user=%r", project_key, file, _user)
        p = queries.project(project_key=project_key, user_id=_user.user_id)
        if not p:
            raise cls.NotFound()

        bucket = "rustybrooks-cadcam"
        storage_key = '{}/{}/{}'.format(_user.user_id, project_key, file.name)

        logger.warn("name=%r, bucket=%r, storage_key=%r", file.name, bucket, storage_key)
        s3.put_object(Body=file, Bucket=bucket, Key=storage_key)
        project_file_id = queries.add_or_update_project_file(
            project_id=p.project_id,
            file_name=file.name,
            s3_key=storage_key,
            source_project_file_id=None,
        )

        if os.path.splitext(file.name)[-1].lower() == '.zip':
            with zipfile.ZipFile(file) as z:
                for i in z.infolist():
                    storage_key = '{}/{}/{}'.format(_user.user_id, project_key, i.filename)
                    with z.open(i) as zf:
                        logger.warn("uploading %r to %r", i.filename, storage_key)
                        s3.put_object(Body=zf.read(), Bucket=bucket, Key=storage_key)
                        queries.add_or_update_project_file(
                            project_id=p.project_id,
                            file_name=i.filename,
                            s3_key=storage_key,
                            source_project_file_id=project_file_id,
                        )

        return {
            'status': 'ok'
        }