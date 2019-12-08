# import bson
from collections import defaultdict
import copy
import datetime
import dateutil.parser
import decimal
import functools
import inspect
import json
import logging
# import newrelic.agent
import os
import pytz

import logging
import time

logger = logging.getLogger(__name__)


class Timer(object):
    def __init__(self, label):
        self.marks = []
        self.label = label

        self.current_label = 0
        self.mark('start')

    def mark(self, label=None):
        label = label or self.current_label
        self.current_label += 1
        self.marks.append((label, time.time()))

    def log_marks(self):
        self.mark('end')
        out = []
        for m1, m2 in zip(self.marks[:-1], self.marks[1:]):
            out.append("%s-%s=%d" % (m1[0], m2[0], 1000 * (m2[1] - m1[1])))

        out.append("total=%d" % (1000 * (self.marks[-1][1] - self.marks[0][1]),))
        logger.warn("%s: %s", self.label, ' - '.join(out))


class OurJSONEncoder(json.JSONEncoder):
    # @newrelic.agent.function_trace()
    def default(self, obj):
        if hasattr(obj, "to_json"):
            return obj.to_json()
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        # elif isinstance(obj, bson.ObjectId):
        #     return str(obj)
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif callable(obj):
            return obj.__name__

        return json.JSONEncoder.default(self, obj)


class Api(object):
    version_fun = defaultdict(dict)
    fn_config = defaultdict(dict)
    wrapper_lookup = {}

    class APIException(Exception):
        status_code = 500
        default_detail = 'A server error occured'

        def __init__(self, detail=None, status_code=None):
            self.detail = detail or self.default_detail
            if status_code is not None:
                self.status_code = status_code

        def __str__(self):
            return self.detail

    class NotFound(APIException):
        default_detail = "Not Found"
        status_code = 404

    class Unauthorized(APIException):
        default_detail = "Unauthorized"
        status_code = 401

    class Forbidden(APIException):
        default_detail = "Forbidden"
        status_code = 403

    class BadRequest(APIException):
        default_detail = "Bad Request"
        status_code = 400

    class NotAcceptable(APIException):
        default_detail = "Not Acceptable"
        status_code = 406

    def __init__(self):
        pass

    @classmethod
    def config(cls, *args, **kwargs):
        if '<data>' in args:
            raise Exception("<data> is a reserved keyword in API functions")

        def makewrap(f):
            for a in args:
                cls.fn_config[cls._unwrap(f)].update(a)
            cls.fn_config[cls._unwrap(f)].update(kwargs)
            return f

        return makewrap

    @classmethod
    def _unwrap(cls, f):
        if f.__name__ not in ['wrap']:
            return f

        if f not in cls.wrapper_lookup:
            return None

        return cls._unwrap(cls.wrapper_lookup[f])

    @classmethod
    def _get_args(cls, fn):
        argspec = inspect.getargspec(cls._unwrap(fn))
        border = len(argspec.args or []) - len(argspec.defaults or [])
        list_args = argspec.args[:border]
        keyword_args = list(zip(argspec.args[border:], argspec.defaults or []))
        return [x for x in list_args if x not in ['self', 'cls']], keyword_args, argspec.varargs, argspec.keywords

    @classmethod
    def _get_config(cls, fn):
        return cls.fn_config[fn]

    def _api_functions(self):
        return self.registry.keys()

    def _api_versions(self):
        return self.version_fun.keys()

    def _fn(self, function_name, version='latest'):
        if version == "latest":
            version = max(self.version_fun.keys())

        return self.version_fun[version].get(function_name)

    # allows you to "copy" or "proxy" a function from one API class to another
    def _proxy(self, app, function_name, new_function_name=None, version='latest', kwargs_override=None, **proxy_api_params):
        if version == "latest":
            version = max(self.version_fun.keys() or [None])
        fn = app.version_fun[version][function_name]

        @functools.wraps(fn)
        def _fn(cls, *a, **k):
            if kwargs_override is not None:
                k.update(**kwargs_override)
            return fn(app, *a, **k)

        newfn = _fn
        new_function_name = new_function_name or function_name
        self.version_fun[version][new_function_name] = newfn
        self.fn_config[newfn] = copy.deepcopy(app._get_config(fn))
        self.fn_config[newfn].update(**proxy_api_params)

        if kwargs_override:
            for k, v in kwargs_override.items():
                new_kwargs = self.fn_config[newfn]['fn_args'][1]
                for index, el in enumerate(new_kwargs):
                    if k == el[0]:
                        new_kwargs[index] = (k, v)

        self.registry[new_function_name] = app.registry[function_name]


def api_register(_version=None, **register_kwargs):
    ignore = ['config']

    def class_rebuilder(cls):
        class NewClass(cls):
            registry = {}

            fn_config = copy.deepcopy(cls.fn_config)

            version_fun = copy.deepcopy(cls.version_fun)
            version = _version
            class_name = cls.__name__
            for element in inspect.getmembers(cls, predicate=inspect.ismethod):
                k, v = element
                if k.startswith("_"):
                    continue

                if k in ignore:
                    continue

                # unwrapped = cls._unwrap(v.im_func)
                unwrapped = cls._unwrap(v.__func__)
                individual_config = fn_config[unwrapped]

                # All config params should be set to defaults here
                fn_config[unwrapped] = {
                    'require_admin': False,
                    'require_login': False,
                    'api_key': None,
                    'function_url': None,
                    'param_regexp_map': {},
                    'sort_keys': None,
                    'max_page_limit': -1,
                    'file_keys': None,
                }

                fn_config[unwrapped].update(register_kwargs)
                fn_config[unwrapped].update(individual_config)
                fn_config[unwrapped].update({
                    'version': _version,
                    # 'fn_args': cls._get_args(v.im_func)
                    'fn_args': cls._get_args(v.__func__)
                })
                # version_fun[_version][k] = v.im_func
                version_fun[_version][k] = v.__func__
                registry[k] = v

            def __init__(self, *args, **kargs):
                super(NewClass, self).__init__(*args, **kargs)

        return NewClass

    return class_rebuilder


def route_pieces(fnname, fn, config, canonical=False):
    def _get_regexp(key):
        return config.get('param_regexp_map', {}).get(key, r'(?P<{}>[^\/]+)'.format(key))

    pieces = []
    route = config.get('route', [])

    list_args, key_args, va, kw = config['fn_args']

    api_key = config.get('api_key')

    if isinstance(api_key, str):
        api_key = [api_key]

    api_key_in_list = False
    non_url_args = ['q', 'sort', 'limit', 'page', 'data']  # special params that should only be query args
    if api_key:
        non_url_args.extend(api_key)
        api_key_in_list = all([x in list_args for x in api_key])

    if route:
        pieces.append(os.path.join(*route[1]))
    else:
        # First url (rest friendly)
        foo = []

        # any "api keys" will go before the function name, like
        # /users/rustybrooks/add vs /users/add/rustybrooks
        if api_key_in_list:
            if canonical:
                foo.extend(['<{}>'.format(a) for a in api_key])
            else:
                foo.extend([_get_regexp(a) for a in api_key])

        # any functions not starting with "index" will be in the url between the api keys and
        # the other list args
        if not fnname.startswith('index'):
            foo.append(config['function_url'] or fnname)

        # The rest of the list arguments go after the function name
        if canonical:
            foo += ['<{}>'.format(x) for x in list_args if x not in non_url_args]
        else:
            foo += [_get_regexp(x) for x in list_args if x not in non_url_args]

        route_piece = os.path.join(*foo) if len(foo) else ''
        #if route_piece:
        pieces.append(route_piece)

        # Second url (simple)
        foo = []
        if not fnname.startswith('index'):
            foo.append(config['function_url'] or fnname)

        pieces.append(os.path.join(*foo) if len(foo) else '')

    return pieces


def urls_from_config(urlroot, fnname, fn, config, canonical=False):
    urls = []

    if config['version'] is None:
        urlbase = urlroot
    else:
        urlbase = os.path.join('v{}'.format(config['version']), urlroot)

    pieces = route_pieces(fnname, fn, config, canonical=canonical)

    urls.append(r"^" + os.path.join(urlbase, pieces[0]).rstrip('/') + r'/?$')
    if len(pieces) > 1:
        urls.append(r"^" + os.path.join('_' + urlbase.lstrip('/'), pieces[1]).rstrip('/') + r'/?$')

    return urls


sentinel = object()


# @newrelic.agent.function_trace()
def process_api(fn, api_object, app_blob, blob):
    api_data_orig = blob['api_data']
    blob_api_data = api_data_orig if isinstance(api_data_orig, dict) else {}

    fn_kwargs = blob['fn_kwargs']

    file_keys = app_blob['_config']['file_keys'] or []

    try:
        stored = {k: v for k, v in app_blob['_kwargs']}
        for arg, default in app_blob['combined_args']:
            if arg in fn_kwargs:
                continue

            if arg == 'data':
                fn_kwargs['data'] = api_data_orig
            elif arg in file_keys:
                fn_kwargs[arg] = get_file(blob['request'], arg)
            elif arg in ['_user', '_request']:
                fn_kwargs[arg] = blob[arg[1:]]
            else:
                val = blob_api_data.get(arg, blob['url_data'].get(arg, sentinel))
                if arg in ['limit', 'page']:
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        val = default

                if val is not sentinel:
                    if arg == 'limit' and app_blob['_config']['max_page_limit'] > 0:
                        val = min(val, app_blob['_config']['max_page_limit'])
                    elif arg == 'page' and val > app_blob['_config'].get('max_page', -1) > 0:
                        raise Api.BadRequest(
                            "Maximum allowed value for page parameter for this endpoint is {}".format(
                            app_blob['_config']['max_page']
                            )
                        )
                    elif arg == 'sort' and val and app_blob['_config']['sort_keys'] is not None:
                        sortkey = val
                        if sortkey[0] == '-':
                            sortkey = sortkey[1:]

                        if sortkey not in app_blob['_config']['sort_keys']:
                            raise Api.BadRequest("Invalid 'sort' parameter '{}'.  Allowed values: {}".format(
                                val,
                                ', '.join(app_blob['_config']['sort_keys']),
                            ))

                    stored[arg] = fn_kwargs[arg] = val

                if arg == 'sort' and not val:
                    fn_kwargs[arg] = default

        # newrelic.agent.set_transaction_name(app_blob['_fnname'], group=app_blob['_newrelic_group'])

        # run API function and massage result if required
        api_object._status_code = 200

        retval = fn(api_object, *blob['fn_args'], **fn_kwargs)
    except Api.APIException as e:
        if isinstance(e.detail, str):
            data = {
                'detail': e.detail,
            }
        else:
            data = e.detail

        retval = JSONResponse(
            data=data,
            status=e.status_code,
        )

    # return results
    if isinstance(retval, (HttpResponse, FileResponse, JSONResponse)):
        logger.warn("Returning special response %r", retval.response)
        return retval

    if hasattr(retval, 'items') and 'results' in retval and 'count' in retval \
            and stored.get('page') is not None and stored.get('limit') is not None:
        prev_url = retval.get('previous')
        next_url = retval.get('next')

        if not prev_url and stored['page'] > 1 and (stored['page']-1)*stored['limit'] < retval['count']:
            params = blob['url_data'].copy()
            params['page'] = stored['page'] - 1
            if params.get('limit'):
                params['limit'] = stored['limit']
            prev_url = build_absolute_url(blob['path'], params)

        if not next_url and stored['page'] * stored['limit'] < retval['count']:
            params = blob['url_data'].copy()
            params['page'] = stored['page'] + 1
            if params.get('limit'):
                params['limit'] = stored['limit']
            next_url = build_absolute_url(blob['path'], params)

        retval['previous'] = prev_url
        retval['next'] = next_url

    return JSONResponse(data=retval, status=api_object._status_code)


@api_register()
class FrameworkApi(Api):
    @classmethod
    def endpoints(cls, apps=None, _user=None):
        def _clean_url(url):
            for c in "?^$":
                url = url.replace(c, '')

            url = url.rstrip('/')
            return url

        apps = apps.split(',') if apps else []
        data = {}

        if callable(_user.is_authenticated):
            ia = _user.is_authenticated()
        else:
            ia = _user.is_authenticated

        for urlroot in sorted(app_registry.keys()):
            app = app_registry[urlroot]
            if apps and app.class_name not in apps:
                continue

            these_endpoints = {}
            these_endpoints['__data'] = {
                'url': urlroot
            }
            for version in app._api_versions():
                for fnname in sorted(app._api_functions()):
                    fn = app._fn(fnname, version)
                    config = app._get_config(fn)

                    _require_login = config.get('require_login', False)
                    _require_admin = config.get('require_admin', False)

                    # ensure user is logged in if required
                    # if _require_login or _require_admin:
                    #     if _user is None or not _user.is_authenticated():
                    #         continue

                    # ensure user is admin if required
                    if _require_admin and (not ia or not _user.is_staff):
                        continue

                    urls = urls_from_config(urlroot, fnname, fn, config, canonical=True)
                    list_args, key_args, va, kw = config['fn_args']

                    this = {
                        'app': app.class_name,
                        'function': fnname,
                        'simple_url': _clean_url(urls[1] if len(urls) > 1 else urls[0]),
                        'ret_url': _clean_url(urls[0]),
                        'args': list_args,
                        'kwargs': key_args,
                        'config': {k: v for k, v in config.items() if k not in ['fn_args']},
                    }
                    these_endpoints[fnname] = this
            data[app.class_name] = these_endpoints
            data['user'] = {'id': _user.id, 'username': getattr(_user, 'username', None), 'authenticated': ia}

        return data


def api_list(val, split=','):
    if val is None:
        return None

    if isinstance(val, (tuple, list)):
        return val

    return val.split(split)


def api_bool(val):
    if val is None:
        return None

    if isinstance(val, bool):
        return val
    elif isinstance(val, int):
        return bool(val)

    if val.lower() == "true":
        return True

    try:
        val = int(val)
        if val:
            return True
    except ValueError:
        pass

    return False


def api_int(intstr, default=0):
    if intstr is None:
        return None

    try:
        return int(intstr)
    except ValueError:
        return default


def api_float(floatstr, default=0):
    if floatstr is None:
        return None

    try:
        return float(floatstr)
    except ValueError:
        return default


def api_datetime(dtstr, default=None):
    if isinstance(dtstr, datetime.datetime):
        dt = dtstr
    else:
        dt = dateutil.parser.parse(dtstr, fuzzy=True) if dtstr else None

    if dt and dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    if not dt and default:
        if not isinstance(default, datetime.datetime):
            default = dateutil.parser.parse(default, fuzzy=True) if dtstr else None

    return dt or default


def test_sort_param():
    missing_sort = []
    for urlroot, app in app_registry.items():
        for version in app._api_versions():
            for fnname in sorted(app._api_functions()):
                fn = app._fn(fnname, version)
                config = app._get_config(fn)

                list_args, key_args, va, kw = config['fn_args']

                if 'sort' in dict(key_args) and not config['sort_keys']:
                    missing_sort += [[app.class_name, fnname]]

    return missing_sort

def test_limit_param():
    missing_limit = []
    for urlroot, app in app_registry.items():
        for version in app._api_versions():
            for fnname in sorted(app._api_functions()):
                fn = app._fn(fnname, version)
                config = app._get_config(fn)

                list_args, key_args, va, kw = config['fn_args']

                if 'limit' in dict(key_args) and config['max_page_limit'] <= 0:
                    missing_limit += [[app.class_name, fnname]]

    return missing_limit

