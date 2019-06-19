from flask import Flask
import logging
import os

from lib.api_framework import api_register, Api, app_class_proxy
from flask_cors import CORS

from . import pcb

root = os.path.join(os.path.dirname(__file__))

logger = logging.getLogger(__name__)
logging.basicConfig()

logger.warn("....1")

app = Flask('cadcam-api', template_folder=os.path.join(root, 'templates'), static_folder=os.path.join(root, 'static'))
CORS(app)

logger.warn("....2")


@api_register(None, require_login=False)
class TestApi(Api):
    @classmethod
    def index(cls):
        return "hi"

logger.warn("....3")

app_class_proxy(app, '', 'api/test', TestApi())
app_class_proxy(app, '', 'api/pcb', pcb.PCBApi())

logger.warn("....4")
