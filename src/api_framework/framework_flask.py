from collections import defaultdict
import functools
import json
import logging
# import newrelic.agent
import os
# from otxb_core_utils.config import ConfigUtils
import traceback

from . import utils

app_registry = {}
logger = logging.getLogger(__name__)
# SECRETO = ConfigUtils.get_value("auth-secret")

from flask import Response, request


def build_absolute_url(path, params):
    return ""


# for compatibility with Django
class HttpResponse(Response):
    def __init__(self, content, status=200, content_type='text/html'):
        super(HttpResponse, self).__init__(
            response=content,
            content_type=content_type,
            status=status
        )


class FileResponse(Response):
    pass


class FlaskUser(object):
    def __init__(self, token, profile, otx_key):
        self.profile = profile
        self.token = token
        self.otx_key = otx_key
        self.is_staff = False

        # logger.warn("secret=%r, otx_key=%r, bool=%r", SECRETO, otx_key, SECRETO and SECRETO == otx_key)
        if profile:
            self.username = profile['username']
            self.id = profile['user_id']
        # elif SECRETO and SECRETO == otx_key:
        #     self.username = 'Token'
        #     self.id = 1
        else:
            self.username = 'Anonymous'
            self.id = 0

    def is_authenticated(self):
        return self.id != 0


class JSONResponse(Response):
    # @newrelic.agent.function_trace()
    def __init__(self, data=None, detail=None, err=False, status=None):
        if not status:
            status = 400 if err else 200

        self._data = data if data is not None else {}  # fixme causes error
        if detail:
            self._data['detail'] = detail

        super(JSONResponse, self).__init__(
            response=json.dumps(self._data, cls=utils.OurJSONEncoder),
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


# @newrelic.agent.function_trace()
def parse_json():
    return request.get_json()


def app_proxy(sa, fn, fnname, config, urlroot, cleanup_callback=None):
    _require_login = config.get('require_login', False)
    _require_admin = config.get('require_admin', False)
    app_blob = {
        '_newrelic_group': os.path.join('/', urlroot).rstrip('/'),
        '_fnname': fnname,
       '_config': config,
    }
    app_blob['_args'], app_blob['_kwargs'], app_blob['_va'], app_blob['_kw'] = config['fn_args']
    app_blob['combined_args'] = app_blob['_kwargs'] + [(x, None) for x in app_blob['_args']]

    @functools.wraps(fn)
    def appfn(*fn_args, **fn_kwargs):
        doer = sa()

        payload = None
        token = None
        # token = request.headers.get('authorization')
        # if 'authorization' in request.headers:
        #     logger.warn("Looking up auth0 token payload...")
        #     from otxb_core_utils.api import auth0
        #     payload = auth0.token_payload(token)

        user = FlaskUser(token, payload, otx_key=request.headers.get('otx-authorization-key'))

        api_data = parse_json() or request.form
        url_data = request.args
        blob = {
            'fn_args': fn_args,
            'fn_kwargs': fn_kwargs,
            'path': request.path,
            'user': user,
            'request': request,
            'api_data': api_data,
            'url_data': url_data,
        }

        # ensure user is logged in if required
        # logger.warn("path=%r, user=%r, require=%r/%r, auth=%r", request.full_path, user.id, _require_login, _require_admin, user.is_authenticated())
        if (_require_login or _require_admin) and not user.is_authenticated():
            return JSONResponse(detail='Authentication required', status=403)

        # ensure user is admin if required
        if _require_admin:
            return JSONResponse(detail="Admin accounts not enabled", status=403)

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
                view_name = '{}-{}-{}'.format(urlroot.replace('/', '_'), fnname, counts[fnname])
                logger.info("Adding url %r to %r", u, view_name)
                base_app.add_url_rule(
                    u,
                    endpoint=view_name,
                    view_func=app_proxy(app.__class__, fn, fnname, config, urlroot, cleanup_callback=cleanup_callback),
                    methods=['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'HEAD']
                )
                counts[fnname] += 1

