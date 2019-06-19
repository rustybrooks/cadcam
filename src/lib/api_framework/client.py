import contextlib
import copy
import functools
import json
import logging
import os
from otxb_core_utils.config import ConfigUtils
from otxb_core_utils.api.framework.utils import OurJSONEncoder, Api
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


session = requests.session()
retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=.25,
        status_forcelist=(500, 429, 502, 503, 504),
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)


class FrameworkEndpoint(object):
    def __init__(self, framework, command):
        self.framework = framework
        self.command = command

    def __call__(self, *args, **kwargs):
        headers = self.framework._headers.copy()

        cmd = self.framework.api_data[self.command]
        url = cmd['simple_url']
        if 'data' in kwargs:
            data = kwargs['data']   # FIXME
        else:
            data = {}
            for k, v in zip(args, cmd['args']):
                data[k] = v
            data.update(kwargs)

        whole_url = os.path.join(self.framework._base_url, url)
        file_keys = cmd['config'].get('file_keys')
        files = {}
        if file_keys:
            for fk in file_keys:
                file_param = data.pop(fk, None)
                if not file_param:
                    continue

                if hasattr(fk, 'read'):
                    files[fk] = (data.pop('{}_name'.format(fk), 'unknown'), file_param, 'application/octet-stream')
                else:
                    files[fk] = (os.path.split(file_param)[-1], open(file_param, 'rb'), 'application/octet-stream')

                files['data'] = json.dumps(data, cls=OurJSONEncoder)

            logger.warn("framework client upload, url=%r, headers=%r, files=%r", whole_url, headers, files)
            r = session.post(whole_url, files=files, headers=headers)
        else:
            headers['Content-Type'] = 'application/json'
            r = session.post(whole_url, data=json.dumps(data, cls=OurJSONEncoder), headers=headers)

        if r.status_code >= 300:
            for code, exc in (
                (400, Api.BadRequest),
                (401, Api.Unauthorized),
                (403, Api.Forbidden),
                (404, Api.NotFound),
                (406, Api.NotAcceptable),
                (500, Api.APIException),
            ):
                if r.status_code == code:
                    try:
                        raise exc(r.json())
                    except:
                        raise exc({'content': r.content})

            raise Exception("Error in framework client: url=%r, data=%r, files=%r, code=%d return=%s" % (
                whole_url, data, files, r.status_code, r.content
            ))
        try:
            return r.json()
        except:
            return r.content

    def walk(self, *args, **kwargs):
        stop_limit = kwargs.pop('stop_limit', None)
        kwargs['page'] = kwargs.get('page', 1)

        count = 0
        while True:
            r = self(*args, **kwargs)
            for res in r['results']:
                yield res
                count += 1

                if stop_limit and count == stop_limit:
                    return

            if not r['next']:
                break

            kwargs['page'] += 1

    def info(self):
        return self.framework.api_data[self.command]


class Framework(object):
    def __init__(self, base_url, headers, api_data):
        self._base_url = base_url
        self.api_data = api_data
        self._headers = headers

    def __getattr__(self, command):
        return FrameworkEndpoint(self, command)

    # This proxies a function FROM this client, TO a framework app.  I know, it's weird.
    def proxy(self, app, function_name, new_function_name=None, kwargs_override=None, kwargs_add=None, wrapper=None, **proxy_api_params):
        version = None
        fwe = getattr(self, function_name)
        api_data = self.api_data[function_name]
        fn = fwe.__call__
        if wrapper:
            fn = wrapper(fn)

        @functools.wraps(fn)
        def _fn(cls, *a, **k):
            return fn(app, *a, **k)

        list_args = api_data['args']
        key_args = api_data['kwargs']
        va = kw = None  # Not sure if needed

        newfn = _fn
        new_function_name = new_function_name or function_name
        app.version_fun[version][new_function_name] = newfn
        app.fn_config[newfn] = copy.deepcopy(api_data['config'])
        app.fn_config[newfn].update({
            'fn_args': [list_args, key_args, va, kw],
            'version': None,
        })
        app.fn_config[newfn].update(proxy_api_params)

        if kwargs_override:
            new_kwargs = app.fn_config[newfn]['fn_args'][1]
            for k, v in kwargs_override.items():
                for index, el in enumerate(new_kwargs):
                    if k == el[0]:
                        new_kwargs[index] = (k, v)

        if kwargs_add:
            new_kwargs = app.fn_config[newfn]['fn_args'][1]
            for k, v in kwargs_add.items():
                new_kwargs.append((k, v))

        app.registry[new_function_name] = None

    def list_functions(self):
        return [x for x in self.api_data.keys() if not x.startswith('_')]


class Frameworks(object):
    def __init__(self, base_url, framework_endpoint, framework_key=None, headers=None, privileged_key=None, save_path=None, load_cache=False):
        self._headers = headers or {}
        self._base_url = base_url
        self._framework_endpoint = framework_endpoint
        self._endpoints = None
        self._framework_key = framework_key
        self._privileged_key = privileged_key
        self._save_path = os.path.join(save_path, self._framework_key) + '.json' if save_path else None
        self._load_cache = load_cache

    def lazy_load(self, load_cache=False):
        if self._endpoints:
            return

        load_cache = self._load_cache or load_cache
        logger.warn("load_cache=%r, save_path=%r", load_cache, self._save_path)
        if load_cache and self._save_path and os.path.exists(self._save_path):
            logger.warn("Loading framework data from %r", self._save_path)
            # FIXME we need a try/catch but I don't know what to look for
            with open(self._save_path) as f:
                self._endpoints = json.load(f)
            return

        if self._base_url is None:
            raise Exception("Did not find framework matching the name '{}'".format(self._framework_key))

        these_headers = {}
        these_headers.update(self._headers)
        if self._privileged_key:
            these_headers['X-OTX-API-KEY'] = self._privileged_key
            these_headers['OTX-AUTHORIZATION-KEY'] = self._privileged_key

        url = os.path.join(self._base_url, self._framework_endpoint)
        r = session.get(url, headers=these_headers)
        if r.status_code >= 300:
            raise Exception("Status code %d encountered while trying to get framework endpoint: %r" % (r.status_code, url))
        try:
            self._endpoints = r.json()
        except Exception, e:
            raise Exception("Framework endpoint did not return data: url=%r, error=%r" % (url, e))

    def __getattr__(self, apiname):
        if apiname.startswith('_'):
            return self.__dict__.get('apiname')

        self.lazy_load()
        return Framework(self._base_url, self._headers, self._endpoints[apiname])

    def list_apis(self):
        self.lazy_load()
        return self._endpoints.keys()

    def list_endpoints(self):
        self.lazy_load()
        return {x: [foo for foo in y.keys() if not foo.startswith('_')] for x, y in self._endpoints.items()}

    @contextlib.contextmanager
    def manage_otxp_login(self, *args, **kwargs):
        oldcreds = self._headers.copy()
        self.otxp_login(*args, **kwargs)

        yield

        self._headers = oldcreds

    def otxp_login(self, username=None, password=None, key=None, headers=None):
        self._headers.update(headers or {})

        if headers and not (username or password or key):
            return
        elif key:
            self._headers['X-OTX-API-KEY'] = key
            return self
        else:
            data = {'username': username, 'password': password}
            r = session.post('{}auth/login'.format(self._base_url), data)
            if r.status_code != 200:
                raise Exception("Failed to log into OTX with username/password: status_code={}".format(r.status_code))

            self._headers['AUTHORIZATION'] = r.json()['key']

        return self

    def otxb_login(self, secret=None):
        self._headers["otx-authorization-key"] = secret or ConfigUtils.get_value("auth-secret")
        return self

    def materialize(self):
        logger.warn("Saving framework data to %r", self._save_path)
        self.lazy_load(load_cache=False)
        with open(self._save_path, 'w') as f:
            json.dump(self._endpoints, f)


def factory(framework, **kwargs):
    fw = ConfigUtils.get_value("api_frameworks")
    base_url, framework_endpoint = fw.get(framework, [None, None])
    return Frameworks(
        base_url=base_url,
        framework_endpoint=framework_endpoint,
        framework_key=framework,
        **kwargs
    )


