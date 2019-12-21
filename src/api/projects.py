import boto3
import datetime
import logging
import os
import pytz
import zipfile

from lib.api_framework import api_register, Api, FileResponse
from lib import config

from . import queries

logger = logging.getLogger(__name__)

bucket = "rustybrooks-cadcam-{}".format(config.get_config_key('ENVIRONMENT'))

s3 = boto3.client(
    's3',
    aws_access_key_id=config.get_config_key('aws_access_key_id'),
    aws_secret_access_key=config.get_config_key('aws_secret_access_key')
)


class FileStore(object):
    def __init__(self, basedir=None, use_s3=False):
        self.use_s3 = use_s3
        self.basedir = os.path.abspath(basedir)

    def _save(self, storage_key, fobj):
        file_name = os.path.abspath(os.path.join(self.basedir, storage_key))
        if not file_name.startswith(self.basedir):
            raise Exception("No file shenanigans allowed")

        dir = os.path.dirname(file_name)
        if not os.path.exists(dir):
            os.makedirs(dir)

        logger.warn("Uploading %r to %r", file_name, storage_key)
        with open(file_name, 'wb+') as f:
            f.write(fobj.read())

        # s3.put_object(Body=fobj, Bucket=bucket, Key=storage_key)
        if self.use_s3:
            s3.upload_file(file_name, Bucket=bucket, Key=storage_key)

    def get(self, project_file_id=None, project_file=None):
        if project_file:
            pf = project_file.copy()
        else:
            pf = queries.project_file(project_file_id=project_file_id)

        file_name = os.path.join(self.basedir, pf['s3_key'])

        if self.use_s3:
            if os.path.exists(file_name):
                file_date = os.path.getmtime(file_name)
            else:
                file_date = 0

            offset = (pytz.utc.localize(pf['date_uploaded']) - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()
            if file_date - offset < 120:
                s3.download_file(bucket, pf['s3_key'], file_name)

        return file_name

    def get_fobj(self, project_file_id=None, project_file=None):
        file_name = self.get(project_file_id=project_file_id, project_file=project_file)
        return open(file_name)

    def add(self, project_key=None, project_job_id=None, fobj=None, user_id=None, file_name=None, project=None, split_zip=False):
        logger.warn("adding... key=%r, user_id=%r", project_key, user_id)
        if project is None:
            project = queries.project(project_key=project_key, user_id=user_id)
            if not project:
                return 'project not found'
        else:
            user_id = user_id if user_id else project['user_id']

        if project_job_id:
            storage_key = '{}/{}/{}/{}'.format(user_id, project['project_key'], project_job_id, file_name)
        else:
            storage_key = '{}/{}/{}'.format(user_id, project['project_key'], file_name)
        self._save(storage_key, fobj)
        project_file_id = queries.add_or_update_project_file(
            project_id=project['project_id'],
            project_job_id=project_job_id,
            file_name=file_name,
            s3_key=storage_key,
            source_project_file_id=None,
        )

        if os.path.splitext(file_name)[-1].lower() == '.zip' and split_zip:
            with zipfile.ZipFile(fobj) as z:
                for i in z.infolist():
                    file_name = os.path.split(i.filename)[-1]
                    storage_key = '{}/{}/{}'.format(user_id, project_key, file_name)
                    with z.open(i) as zf:
                        self._save(storage_key, zf)
                        queries.add_or_update_project_file(
                            project_id=project['project_id'],
                            project_job_id=project_job_id,
                            file_name=file_name,
                            s3_key=storage_key,
                            source_project_file_id=project_file_id,
                        )

        queries.update_project()

        return None


project_files = FileStore(basedir='/srv/data/project_files')

@api_register(None, require_login=True)
class ProjectsApi(Api):
    @classmethod
    @Api.config(require_login=False)
    def index(cls, username=None, page=1, limit=10, _user=None):
        out = {
            'results': queries.projects(username=username, page=page, limit=limit),
        }

        for r in out['results']:
            r.update({
                'created_ago': (datetime.datetime.utcnow() - r['date_created']).total_seconds(),
                'modified_ago': (datetime.datetime.utcnow() - r['date_modified']).total_seconds(),
            })

        return out

    @classmethod
    @Api.config(require_login=False)
    def project(cls, username=None, project_key=None, _user=None):
        logger.warn("user = %r", _user.__class__)
        p = queries.project(
            project_key=project_key,
            username=username,
            viewing_user_id=_user.user_id,
            allow_public=True,
        )
        if not p:
            raise cls.NotFound()

        p['files'] = queries.project_files(project_id=p['project_id'], is_deleted=False)
        for f in p['files']:
            f['uploaded_ago'] = (datetime.datetime.utcnow() - f['date_uploaded']).total_seconds()
        p['is_ours'] = p['username'] == _user.username

        p.update({
            'created_ago': (datetime.datetime.utcnow() - p['date_created']).total_seconds(),
            'modified_ago': (datetime.datetime.utcnow() - p['date_modified']).total_seconds(),
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
        project = queries.project(project_key=project_key, user_id=_user.user_id)
        if not project:
            raise cls.NotFound()

        error = project_files.add(
            project=project,
            project_key=project_key,
            fobj=file,
            user_id=_user.user_id,
            file_name=os.path.split(file.name)[-1],
            split_zip=True,
        )
        if error:
            raise cls.BadRequest(error)

        return {'status': 'ok'}

    @classmethod
    def delete_file(cls, project_key, project_file_id=None, _user=None):
        p = queries.project(project_key=project_key, username=_user.username)
        if not p:
            raise cls.NotFound()

        pf = queries.project_file(project_id=p['project_id'], project_file_id=project_file_id)
        if not pf:
            raise cls.NotFound()

        queries.delete_project_file(project_file_id=project_file_id)

        return {'status': 'ok'}

    @classmethod
    @Api.config(require_login=False)
    def download_file(cls, file_name, project_file_id=None, as_json=False, _user=None):
        # pf = queries.project_file(project_file_id=project_file_id, user_id=_user.user_id)
        pf = queries.project_file(project_file_id=project_file_id, is_public=True)
        if not pf:
            raise cls.NotFound()

        # project = queries.project(project_id=pf['project_id, user_id=_user.user_id)
        project = queries.project(project_id=pf['project_id'])
        if not project:
            raise cls.NotFound()

        file_name = project_files.get(project_file_id=project_file_id)
        if as_json:
            return {
                'content': open(file_name, 'rb').read(),
            }
        else:
            ext = os.path.splitext(file_name)[-1].lower()
            content_type = 'application/octet-stream'
            if ext in ['.svg']:
                content_type = 'image/svg+xml'

            return FileResponse(
                content=open(file_name, 'rb').read(),
                content_type=content_type,
            )

    @classmethod
    @Api.config(require_login=False)
    def user_projects(self, limit=20):
        return queries.user_projects(limit=limit)


