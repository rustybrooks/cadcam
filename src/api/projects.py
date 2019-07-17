import boto3
import datetime
import logging
import os
import pytz
import zipfile

from lib.api_framework import api_register, Api
from lib import config

from . import queries

logger = logging.getLogger(__name__)

bucket = "rustybrooks-cadcam-{}".format(config.get_config_key('ENVIRONMENT'))

s3 = boto3.client(
    's3',
    aws_access_key_id=config.get_config_key('aws_access_key_id'),
    aws_secret_access_key=config.get_config_key('aws_secret_access_key')
)


class S3Cache(object):
    basedir = '/srv/data/s3cache'

    def get(self, project_file_id=None, project_file=None):
        if project_file:
            pf = project_file.copy()
        else:
            pf = queries.project_file(project_file_id=project_file_id)

        project_path = os.path.join(self.basedir, str(pf.project_id))
        if not os.path.exists(project_path):
            try:
                os.makedirs(project_path)
            except OSError:
                pass

        file_name = os.path.join(project_path, pf.file_name)
        if os.path.exists(file_name):
            file_date = os.path.getmtime(file_name)
        else:
            file_date = 0

        offset = (pytz.utc.localize(pf.date_uploaded) - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
        if file_date - offset < 120:
            s3.download_file(bucket, pf.s3_key, file_name)

        return file_name

    def get_fobj(self, project_file_id=None, project_file=None):
        file_name = self.get(project_file_id=project_file_id, project_file=project_file)
        return open(file_name)

s3cache = S3Cache()


@api_register(None, require_login=True)
class ProjectsApi(Api):
    @classmethod
    @Api.config(require_login=False)
    def index(cls, username=None, page=1, limit=10, _user=None):
        out = {
            'results': queries.projects(username=_user.username if username == 'me' else username, page=page, limit=limit),
        }

        for r in out['results']:
            r.update({
                'created_ago': (datetime.datetime.utcnow() - r.date_created).total_seconds(),
                'modified_ago': (datetime.datetime.utcnow() - r.date_modified).total_seconds(),
            })

        return out

    @classmethod
    @Api.config(require_login=True)
    def my_index(cls, page=1, limit=10, _user=None):
        return cls.index(username='me', page=page, limit=limit, _user=_user)

    @classmethod
    @Api.config(require_login=False)
    def project(cls, username=None, project_key=None, _user=None):
        p = queries.project(
            project_key=project_key,
            username=_user.username if username == 'me' else username,
            viewing_user_id=_user.user_id,
            allow_public=True,
        )
        if not p:
            raise cls.NotFound()

        p['files'] = queries.project_files(project_id=p.project_id, is_deleted=False)
        for f in p['files']:
            f['uploaded_ago'] = (datetime.datetime.utcnow() - f.date_uploaded).total_seconds()
        p['is_ours'] = p.username == _user.username

        p.update({
            'created_ago': (datetime.datetime.utcnow() - p.date_created).total_seconds(),
            'modified_ago': (datetime.datetime.utcnow() - p.date_modified).total_seconds(),
        })

        return p

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
        p = queries.project(project_key=project_key, user_id=_user.user_id)
        if not p:
            raise cls.NotFound()

        file_name = os.path.split(file.name)[-1]
        storage_key = '{}/{}/{}'.format(_user.user_id, project_key, file_name)
        s3.put_object(Body=file, Bucket=bucket, Key=storage_key)
        project_file_id = queries.add_or_update_project_file(
            project_id=p.project_id,
            file_name=file_name,
            s3_key=storage_key,
            source_project_file_id=None,
        )

        if os.path.splitext(file.name)[-1].lower() == '.zip':
            with zipfile.ZipFile(file) as z:
                for i in z.infolist():
                    file_name = os.path.split(i.filename)[-1]
                    storage_key = '{}/{}/{}'.format(_user.user_id, project_key, file_name)
                    with z.open(i) as zf:
                        s3.put_object(Body=zf.read(), Bucket=bucket, Key=storage_key)
                        queries.add_or_update_project_file(
                            project_id=p.project_id,
                            file_name=file_name,
                            s3_key=storage_key,
                            source_project_file_id=project_file_id,
                        )

        return {'status': 'ok'}

    @classmethod
    def delete_file(cls, project_key, project_file_id=None, _user=None):
        p = queries.project(project_key=project_key, username=_user.username)
        if not p:
            raise cls.NotFound()

        pf = queries.project_file(project_id=p.project_id, project_file_id=project_file_id)
        if not pf:
            raise cls.NotFound()

        queries.delete_project_file(project_file_id=project_file_id)

        return {'status': 'ok'}
