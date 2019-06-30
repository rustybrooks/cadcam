from collections import defaultdict
import functools
import json
import logging
# import newrelic.agent
import os
# from otxb_core_utils.config import ConfigUtils
import traceback
import werkzeug.exceptions

from . import utils

app_registry = {}
logger = logging.getLogger(__name__)
# SECRETO = ConfigUtils.get_value("auth-secret")

from flask import Response, request


def build_absolute_url(path, params):
    return ""


# for compatibility with Django
class HttpResponse(Response):
    def __init__(self, content, status=200, content_type='text/html', headers=None):
        super(HttpResponse, self).__init__(
            response=content,
            content_type=content_type,
            status=status,
            headers=headers or {},
        )


class FileResponse(Response):
    def __init__(self, content=None, content_type=None):
        super(FileResponse, self).__init__(
            response=content, content_type=content_type
        )


class RequestFile(object):
    def __init__(self, fobj):
        self.fobj = fobj

    @property
    def name(self):
        return self.fobj.filename

    @property
    def size(self):
        return -1

    def chunks(self):
        while True:
            data = self.fobj.read(1024*32)
            if data:
                yield data
            else:
                return

    def read(self, *args, **kwargs):
        return self.fobj.read(*args, **kwargs)

    def tell(self, *args, **kwargs):
        return self.fobj.tell(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self.fobj.seek(*args, **kwargs)


def get_file(_request, key):
    if key not in _request.files:
        return None

    return RequestFile(_request.files[key])


class FlaskUser(object):
    def __init__(self, username, user_id):
        self.username = username
        self.user_id = user_id
        self.id = user_id
        self.is_staff = False

    def is_authenticated(self):
        return self.id != 0


class JSONResponse(Response):
    # @newrelic.agent.function_trace()
    def __init__(self, data=None, detail=None, err=False, status=None, indent=None):
        if not status:
            status = 400 if err else 200

        self._data = data if data is not None else {}  # fixme causes error
        if detail:
            self._data['detail'] = detail

        super(JSONResponse, self).__init__(
            response=json.dumps(self._data, cls=utils.OurJSONEncoder, indent=indent),
            status=status,
            mimetype='application/json'
        )


class XMLResponse(Response):
    def __init__(self, data=None, detail=None, err=False, status=None, content=None):
        status = status or 200
        self.content = content if content is not None else ""

        super(XMLResponse, self).__init__(
            response=self.content,
            status=status,
            mimetype='application/xml'
        )


def default_login_method(request=None, **kwargs):
    if request.user is None:
        return FlaskUser('Anonymous', 0)
    else:
        return request.user
    # token = request.headers.get('authorization')
    # if 'authorization' in request.headers:
    #     from otxb_core_utils.api import auth0
    #     payload = auth0.token_payload(token)
    #     return FlaskUser(payload['username'], payload['user_id'])
    #
    # return


def app_proxy(sa, fn, fnname, config, urlroot, cleanup_callback=None):
    _require_login = config.get('require_login', False)
    _require_admin = config.get('require_admin', False)
    app_blob = {
        '_newrelic_group': os.path.join('/', urlroot).rstrip('/'),
        '_fnname': fnname,
       '_config': config,
    }
    app_blob['_args'], app_blob['_kwargs'], app_blob['_va'], app_blob['_kw'] = config['fn_args']
    app_blob['combined_args'] = list(app_blob['_kwargs']) + [(x, None) for x in app_blob['_args']]

    @functools.wraps(fn)
    def appfn(*fn_args, **fn_kwargs):
        doer = sa()

        try:
            if request.data:
                api_data = request.get_json()
            else:
                api_data = request.form
        except werkzeug.exceptions.BadRequest as e:
            logger.warn("werkzeug.exceptions.BadRequest: url=%r, data=%r, headers=%r", request.path, request.data, [])
            raise e

        url_data = request.args
        login_fn = _require_login if callable(_require_login) else default_login_method
        blob = {
            'fn_args': fn_args,
            'fn_kwargs': fn_kwargs,
            'path': request.path,
            'request': request,
            'api_data': api_data,
            'url_data': url_data,
            'user': login_fn(request=request, api_data=api_data, url_data=url_data)
        }

        # ensure user is logged in if required
        if (_require_login or _require_admin):
            if not blob['user']:
                return JSONResponse(detail='Authentication required', status=403)

            if callable(blob['user'].is_authenticated):
                ia = blob['user'].is_authenticated()
            else:
                ia = blob['user'].is_authenticated

            if not ia:
                return JSONResponse(detail='Authentication required', status=403)

        # ensure user is admin if required
        if _require_admin and not blob['user'].is_admin:
            return JSONResponse(detail="Authentication required", status=403)

        # This does not handle file uploads, fix later
        val = utils.process_api(fn, doer, app_blob, blob)
        if cleanup_callback:
            try:
                cleanup_callback()
            except Exception as e:
                logger.error("Error performing cleanup callback: %r", traceback.format_exc())

        return val

    return appfn


def app_class_proxy(base_app, urlprefix, urlroot, app, cleanup_callback=None):
    counts = defaultdict(int)
    app_registry[urlroot] = app
    for fnname in app._api_functions():
        for version in app._api_versions():
            fn = app._fn(fnname, version)
            config = app._get_config(fn)

            for u in utils.urls_from_config(urlroot, fnname, fn, config, canonical=True):
                u = os.path.join("/", urlprefix, u.lstrip("/^").rstrip("/?$"))
                view_name = '{}-{}-{}-{}'.format(
                    urlprefix.replace('/', '_'),
                    urlroot.replace('/', '_'),
                    fnname,
                    counts[fnname]
                )
                logger.info("Adding url %r to %r", u, view_name)
                base_app.add_url_rule(
                    u,
                    endpoint=view_name,
                    view_func=app_proxy(app.__class__, fn, fnname, config, urlroot, cleanup_callback=cleanup_callback),
                    methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'HEAD']
                )
                counts[fnname] += 1

