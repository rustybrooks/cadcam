from flask import Flask, render_template, redirect
# import flask_login
import logging
import os

from lib.api_framework import api_register, Api, app_class_proxy, api_list, api_bool, HttpResponse, utils
from lib import config
from . import migrations
from flask_cors import CORS

from . import pcb, queries, login


root = os.path.join(os.path.dirname(__file__))

logger = logging.getLogger(__name__)
logging.basicConfig()

app = Flask('cadcam-api', template_folder=os.path.join(root, 'templates'), static_folder=os.path.join(root, 'static'))
CORS(app)

app.secret_key = config.get_config_key('app_secret')


# login_manager = flask_login.LoginManager()
# login_manager.init_app(app)

# @login_manager.user_loader
# def load_user(user_id):
#     return queries.User(user_id=user_id, is_authenticated=True)


@api_register(None, require_login=login.is_logged_in, require_admin=True)
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
            apply_versions=api_list(apply)
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


@api_register(None, require_login=login.is_logged_in)
class UserApi(Api):
    # @classmethod
    # @Api.config(require_login=False)
    # def login(cls, username=None, password=None):
    #     if username and password:
    #         user = queries.User(username=username, password=password)
    #         if user.is_authenticated:
    #             flask_login.login_user(user)
    #         else:
    #             return HttpResponse(render_template('login.html'))
    #     else:
    #         return HttpResponse(render_template('login.html'))

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
                logger.warn("user = %r - %r", user, user.generate_token())
                return user.generate_token()

        return None

    @classmethod
    def change_password(cls, new_password=None, _user=None):
        queries.update_user(user_id=_user.user_id, password=new_password)


app_class_proxy(app, '', 'api/admin', AdminApi())
app_class_proxy(app, '', 'api/user', UserApi())
app_class_proxy(app, '', 'api/pcb', pcb.PCBApi())
app_class_proxy(app, '', 'api/framework', utils.FrameworkApi())
