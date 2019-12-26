from lib.api_framework.utils import *
from lib.api_framework import utils

import logging

logging.warn("waht")

# FIXME This is crude - find a better way to control or detect environment
if os.getenv('DJANGO_SETTINGS_MODULE') is not None:
    logging.warn("import from django")
    from .framework_django import *
else:
    logging.warn("import from flask")
    from .framework_flask import *


utils.app_registry = app_registry
utils.HttpResponse = HttpResponse
utils.JSONResponse = JSONResponse
utils.XMLResponse = XMLResponse
utils.FileResponse = FileResponse
utils.build_absolute_url = build_absolute_url
utils.RequestFile = RequestFile
utils.get_file = get_file

