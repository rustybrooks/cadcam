import bcrypt
import datetime
import hashlib
import jwt
import logging
import os
import random


from lib.database.sql import SQLBase
from lib import config
logger = logging.getLogger(__name__)


_SQL = None
JWT_SECRET = config.get_config_key('jwt_secret')


def SQLFactory(sql_url=None, flask_storage=False):
    global _SQL
    if _SQL is None:
        logger.warning("Initializing SQL: %r, flask_storage=%r", sql_url, flask_storage)
        _SQL = SQLBase(
            sql_url,
            echo_pool=True,
            pool_recycle=60*60*2,
            flask_storage=flask_storage,

        )
        logger.warning("Done Initializing SQL: %r, flask_storage=%r", sql_url, flask_storage)

    return _SQL


if config.get_config_key('ENVIRONMENT') == 'dev':
    sql_url = "postgresql://wombat:1wombat2@local-cadcam-postgres.aveng.us:5432/cadcam"
else:
    sql_url = 'postgresql://flannelcat:{}@flannelcat-postgres.cwrbtizazqua.us-west-2.rds.amazonaws.com:5432/cadcam'.format(
        config.get_config_key('DB_PASSWORD')
    )

SQL = SQLFactory(sql_url, flask_storage=os.environ.get('FLASK_STORAGE', "0'") != "0")


class User(object):
    def __unicode__(self):
        return u"User(username={}, user_id={})".format(getattr(self, 'username'), getattr(self, 'user_id'))

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return self.__unicode__()

    def to_json(self):
        return {
            'user_id': self.user_id,
        }

    def __init__(self, api_key=None, user_id=None, username=None, email=None, password=None, is_authenticated=False):
        self.is_authenticated = is_authenticated
        self.is_active = False
        self.is_anonymous = False
        self.user_id = 0

        where, bindvars = SQL.auto_where(api_key=api_key, username=username, user_id=user_id, email=email)

        query = "select * from users {}".format(SQL.where_clause(where))
        r = SQL.select_0or1(query, bindvars)

        if r:
            for k, v in r.items():
                setattr(self, k, v)

            if api_key is not None:
                self.is_authenticated = True
                self.is_active = self.is_authenticated

            if password is not None:
                self.authenticate(password)

    def authenticate(self, password):
        salt = self.password[:29].encode('utf-8')
        genpass = self.generate_password_hash(password, salt)
        ourpass = bytes(self.password.encode('utf-8'))
        logger.warning("%r salt=%r, ourpass=%r, genpass=%r", password, salt, ourpass, genpass)
        self.is_authenticated = ourpass and (genpass == ourpass)
        self.is_active = self.is_authenticated
        return self.is_authenticated

    @classmethod
    def generate_password_hash(cls, password, salt):
        return bcrypt.hashpw(password.encode('utf-8'), salt)

    def get_id(self):
        return str(self.user_id)

    def generate_token(self):
        payload = {
            'user_id': self.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        logger.warn("payload = %r, secret=%r", payload, JWT_SECRET)
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def add_user(username=None, email=None, password=None, is_admin=False):
    salt = bcrypt.gensalt(12)
    return SQL.insert('users', {
        'username': username,
        'email': email,
        'password': User.generate_password_hash(password, salt).decode('utf-8'),
        'api_key': hashlib.sha256(str(random.getrandbits(128))).hexdigest(),
        'is_admin': is_admin,
    })


def update_user(user_id=None, refresh_token=None, access_token=None, expires_at=None, password=None):
    if password is not None:
        salt = bcrypt.gensalt(12)
        password = User.generate_password_hash(password, salt)

    new_data = {
        'refresh_token': refresh_token,
        'access_token': access_token,
        'expires_at': expires_at,
        'password': password,
    }
    data = {k: v for k, v in new_data.items() if v is not None}
    SQL.update('users', 'user_id=:user_id', where_data={'user_id': user_id}, data=data)


def delete_user(username=None, email=None):
    where, bindvars = SQL.auto_where(username=username, email=email)
    SQL.delete('users', where, bindvars)


def users(username=None):
    query = "select * from users"
    return list(SQL.select_foreach(query))


#############################################
# projects

def project(user_id=None, project_key=None):
    r = projects(user_id=user_id, project_key=project_key, limit=2)

    if len(r) > 1:
        raise Exception("Expected 0 or 1 result, found {}".format(len(r)))

    return r[0] if r else None


def projects(user_id=None, project_key=None, page=None, limit=None, sort=None):
    where, bindvars = SQL.auto_where(user_id=user_id, project_key=project_key)
    query = """
        select project_id, project_key, name, date_created, date_modified
        from projects
        {where}
        {sort} {limit}
    """.format(
        where=SQL.where_clause(where),
        sort=SQL.orderby(sort),
        limit=SQL.limit(page=page, limit=limit)
    )

    logger.warn("%r - %r", query, bindvars)

    return list(SQL.select_foreach(query, bindvars))


def add_project(user_id=None, project_key=None, name=None, project_type=None):
    now = datetime.datetime.utcnow()
    SQL.insert('projects', {
        'user_id': user_id,
        'project_key': project_key,
        'name': name,
        'project_type': project_type,
        'date_created': now,
        'date_modified': now,
    })


#############################################
# project_files

def project_file(project_id=None, project_key=None, user_id=None, file_name=None):
    r = project_files(project_id=project_id, project_key=project_key, user_id=user_id, file_name=file_name)
    if len(r) > 1:
        raise Exception("Expected 0 or 1 result, found {}".format(len(r)))

    return r[0] if r else None


def project_files(project_id=None, project_key=None, user_id=None, file_name=None, page=None, limit=None, sort=None):
    where, bindvars = SQL.auto_where(project_id=project_id, project_key=project_key, user_id=user_id, file_name=file_name)
    query = """
        select project_id, project_file_id, user_id, file_name, s3_key, source_project_file_id, date_uploaded
        from projects p 
        join project_files pf using (project_id)
        {where} {sort} {limit}
    """.format(
        where=SQL.where_clause(where),
        sort=SQL.orderby(sort),
        limit=SQL.limit(page=page, limit=limit)
    )

    return list(SQL.select_foreach(query, bindvars))


def add_project_file(project_id=None, file_name=None, s3_key=None, source_project_file_id=None):
    r = SQL.insert(
        'project_files',
        {
            'project_id': project_id,
            'file_name': file_name,
            's3_key': s3_key,
            'source_project_file_id': source_project_file_id,
            'date_uploaded': datetime.datetime.utcnow(),
        }
    )
    return r.project_file_id


def update_project_file(project_file_id, s3_key=None, source_project_file_id=None):
    SQL.update(
        'project_files',
        where='project_file_id=:project_file_id',
        where_data={'project_file_id': project_file_id},
        data={
            's3_key': s3_key,
            'source_project_file_id': source_project_file_id,
            'date_uploaded': datetime.datetime.utcnow(),
        }
    )
    return project_file_id

def add_or_update_project_file(project_id=None, file_name=None, s3_key=None, source_project_file_id=None):
    p = project_file(project_id=project_id, file_name=file_name)
    if p:
        return update_project_file(project_file_id=p.project_file_id, s3_key=s3_key, source_project_file_id=source_project_file_id)
    else:
        return add_project_file(project_id=project_id, file_name=file_name, s3_key=s3_key, source_project_file_id=source_project_file_id)
