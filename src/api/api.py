from collections import defaultdict
import copy
from flask import Flask, request, render_template, request
# import json
import logging
import os

from lib import api_framework, client, config
from lib.api_framework import api_register, Api, HttpResponse, api_bool
from flask_cors import CORS

root = os.path.join(os.path.dirname(__file__))

logger = logging.getLogger(__name__)
app = Flask('cadcam-api', template_folder=os.path.join(root, 'templates'), static_folder=os.path.join(root, 'static'))
CORS(app)




@api_register(None, require_login=False)
class TestApi(Api):
    @classmethod
    def index(cls):
	return "hi"


api_framework.app_class_proxy(app, '', 'api/test', TestApi())
