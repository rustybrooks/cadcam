from flask import Flask, render_template, redirect
import flask_login
import logging
import os

from lib.api_framework import api_register, Api, app_class_proxy, api_list, api_bool, HttpResponse
from lib.database.sql import Migration
from flask_cors import CORS

from . import pcb, queries


root = os.path.join(os.path.dirname(__file__))

logger = logging.getLogger(__name__)
logging.basicConfig()

app = Flask('cadcam-api', template_folder=os.path.join(root, 'templates'), static_folder=os.path.join(root, 'static'))
CORS(app)

app.secret_key = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'


login_manager = flask_login.LoginManager()
login_manager.init_app(app)


def is_logged_in(request, api_data, url_data):
    return flask_login.current_user


@login_manager.user_loader
def load_user(user_id):
    return queries.User(user_id=user_id, is_authenticated=True)


@api_register(None, require_login=is_logged_in, require_admin=True)
class AdminApi(Api):
    @classmethod
    def migrate(cls, apply=None, initial=False):
        return Migration.migrate(
            SQL=queries.SQL,
            dry_run=False,
            initial=api_bool(initial),
            apply_versions=api_list(apply)
        )


@api_register(None, require_login=is_logged_in())
class UserApi(Api):
    @classmethod
    @Api.config(require_login=False)
    def login(cls, username=None, password=None):
        if username and password:
            user = queries.User(username=username, password=password)
            if user.is_authenticated:
                flask_login.login_user(user)
            else:
                return HttpResponse(render_template('login.html'))
        else:
            return HttpResponse(render_template('login.html'))



app_class_proxy(app, '', 'api/test', AdminApi())
app_class_proxy(app, '', 'api/pcb', pcb.PCBApi())
