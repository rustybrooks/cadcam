from flask import Flask, request
import datetime
import logging
import os

from lib.api_framework import api_register, Api, app_class_proxy, api_list, api_bool, utils
from lib import config
from . import migrations
from flask_cors import CORS

from . import pcb, projects, queries, login


root = os.path.join(os.path.dirname(__file__))

logger = logging.getLogger(__name__)
logging.basicConfig()

app = Flask('cadcam-api', template_folder=os.path.join(root, 'templates'), static_folder=os.path.join(root, 'static'))
CORS(app)

app.secret_key = config.get_config_key('app_secret')


@app.before_request
def before_request():
    request.user = login.is_logged_in(request, None, request.args)


@app.after_request
def cleanup(response):
    try:
        queries.SQL.cleanup_conn(dump_log=False)
    except Exception, e:
        logger.warn("after (path=%r): cleanup failed: %r", request.full_path, e)

    return response


@app.after_request
def apply_is_logged_in(response):
    response.headers["X-LOGGED-IN"] = str(int(bool(request.user and request.user.is_authenticated)))
    return response


@api_register(None, require_login=True, require_admin=True)
class AdminApi(Api):
    @classmethod
    def _bootstrap_admin(cls):
        user = queries.User(username='rbrooks')
        if not user.user_id:
            logger.warn("Adding bootstrapped admin user")
            queries.add_user(
                username='rbrooks',
                password=config.get_config_key('admin_password'),
                email='me@rustybrooks.com',
                is_admin=True,
            )

    @classmethod
    def migrate(cls, apply=None, initial=False):
        val = migrations.Migration.migrate(
            SQL=queries.SQL,
            dry_run=False,
            initial=api_bool(initial),
            apply_versions=[int(x) for x in api_list(apply or [])]
        )

        cls._bootstrap_admin()

        return val

    @classmethod
    @Api.config(require_login=False, require_admin=False)
    def bootstrap(cls):
        if not queries.SQL.table_exists('migrations') or not queries.SQL.select_0or1("select count(*) as count from migrations").count > 0:
            val = cls.migrate(apply=None, initial=False)
        else:
            cls._bootstrap_admin()


@api_register(None, require_login=True)
class UserApi(Api):
    @classmethod
    @Api.config(require_login=False)
    def signup(cls, username, email, password1, password2):
        if password1 != password2:
            return cls.BadRequest("Passwords don't match")

        if len(password1) < 8:
            return cls.BadRequest("Passwords must be at least 8 characters")

        queries.add_user(username=username, password=password1, email=email)

    @classmethod
    @Api.config(require_login=False)
    def api_login(cls, username=None, password=None):
        if username and password:
            user = queries.User(username=username, password=password)
            if user and user.is_authenticated:
                return user.generate_token()

        raise cls.Forbidden()

    @classmethod
    @Api.config(require_login=True)
    def generate_temp_token(cls, _user=None):
        return _user.generate_token(datetime.timedelta(minutes=10))

    @classmethod
    def change_password(cls, new_password=None, _user=None):
        queries.update_user(user_id=_user.user_id, password=new_password)

    @classmethod
    def user(cls, _user):
        return {
            'username': _user.username,
            'user_id': _user.user_id,
        }


app_class_proxy(app, '', 'api/admin', AdminApi())
app_class_proxy(app, '', 'api/user', UserApi())
app_class_proxy(app, '', 'api/projects', projects.ProjectsApi())
app_class_proxy(app, '', 'api/pcb', pcb.PCBApi())
app_class_proxy(app, '', 'api/framework', utils.FrameworkApi())
