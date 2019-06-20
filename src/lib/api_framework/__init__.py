from lib.api_framework.utils import *
from lib.api_framework import utils

# FIXME This is crude - find a better way to control or detect environment
if os.getenv('DJANGO_SETTINGS_MODULE') is not None:
    from .framework_django import *
else:
    from .framework_flask import *


utils.app_registry = app_registry
utils.HttpResponse = HttpResponse
utils.JSONResponse = JSONResponse
utils.XMLResponse = XMLResponse
utils.FileResponse = FileResponse
utils.build_absolute_url = build_absolute_url
utils.RequestFile = RequestFile
utils.get_file = get_file

