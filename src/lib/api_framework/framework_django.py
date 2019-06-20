from django.conf import settings as rs_settings
from django.conf.urls import url
from django.core.files.uploadedfile import UploadedFile
from django.http import HttpResponse, FileResponse
from django.http.multipartparser import MultiPartParserError
import functools
import json
from io import BytesIO
import logging
from newrelic.agent import function_trace
import os
from otxb_core_utils.database.sql import dictobj
import urllib
from . import utils

app_registry = {}
logger = logging.getLogger(__name__)


RequestFile = UploadedFile


def build_absolute_url(path, params):
    return os.path.join(rs_settings.SITE_URL, path.lstrip('/') + "?" + urllib.urlencode(params))


class JSONResponse(HttpResponse):
    def __init__(self, data=None, detail=None, err=False, status=None):
        if not status:
            status = 400 if err else 200

        self.data = data if data is not None else {}
        if detail:
            self.data['detail'] = detail

        super(JSONResponse, self).__init__(
            content=json.dumps(self.data, cls=utils.OurJSONEncoder),
            status=status,
            content_type='application/json'
        )


class XMLResponse(HttpResponse):
    def __init__(self, content=None, status=None):
        status = status or 200
        self.content = content if content is not None else ""

        super(XMLResponse, self).__init__(
            content=self.content,
            status=status,
            content_type='application/xml'
        )


@function_trace()
def app_proxy(sa, fn, fnname, config, urlroot):
    _require_login = config.get('require_login', False)
    _require_admin = config.get('require_admin', False)

    app_blob = {
        '_newrelic_group': os.path.join('/', urlroot),
        '_fnname': fnname,
        '_config': config,
    }
    app_blob['_args'], app_blob['_kwargs'], app_blob['_va'], app_blob['_kw'] = config['fn_args']
    app_blob['combined_args'] = app_blob['_kwargs'] + [(x, None) for x in app_blob['_args']]

    @functools.wraps(fn)
    def appfn(request, *fn_args, **fn_kwargs):
        doer = sa()
        blob = {
            'fn_args': fn_args,
            'fn_kwargs': fn_kwargs,
            'path': request.path,
            'api_data': {},
            'request': request,
            'user': request.user,
            'url_data': request.GET,
        }

        # ensure user is logged in if required
        if _require_login or _require_admin:
            if request.user is None or not request.user.is_authenticated():
                return JSONResponse(detail='Authentication required', status=403)

        # ensure user is admin if required
        if _require_admin and not request.user.is_staff:
            return JSONResponse(detail='Staff user required', status=403)

        # if we have a post body, extract data
        body = request.body
        if body:
            if request.META.get('CONTENT_TYPE', '').startswith('multipart/form-data'):
                if hasattr(request, '_body'):
                    # Use already read data
                    data = BytesIO(request._body)
                else:
                    data = request
                try:
                    request._post, request._files = request.parse_file_upload(request.META, data)
                except MultiPartParserError:
                    request._mark_post_parse_error()
                    raise
            else:
                content_type = request.META.get('CONTENT_TYPE', '').lower()
                if 'json' in content_type or 'javascript' in content_type:
                    try:
                        blob['api_data'] = json.loads(request.body)
                    except ValueError:
                        return JSONResponse(detail="Invalid JSON post data.  Body={}".format(request.body), status=400)

        # prepare arguments to pass to API function
        blob['api_data'] = blob['api_data'] or request.POST
        val = utils.process_api(fn, doer, app_blob, blob)
        return val

    return appfn


def app_class_proxy(urlroot, app):
    app_registry[urlroot] = app
    patterns = []
    for fnname in app._api_functions():
        for version in app._api_versions():
            fn = app._fn(fnname, version)
            config = app._get_config(fn)

            for u in utils.urls_from_config(urlroot, fnname, fn, config):
                logger.info("Adding url %r (%r)", u, fnname)
                patterns.append(url(u, app_proxy(app.__class__, fn, fnname, config, urlroot)))

    return patterns
