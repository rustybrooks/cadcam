import contextlib
import copy
import functools
import json
import logging
import os
from otxb_core_utils.config import ConfigUtils
from otxb_core_utils.api.framework.utils import OurJSONEncoder, Api
import requests

session = requests.session()
logger = logging.getLogger(__name__)


class FrameworkEndpoint(object):
    def __init__(self, framework, command):
        self.framework = framework
        self.command = command

    def __call__(self, *args, **kwargs):
        headers = self.framework.headers.copy()
        headers['Content-Type'] = 'application/json'

        cmd = self.framework.api_data[self.command]
        url = cmd['simple_url']
        if 'data' in kwargs:
            data = kwargs['data']   # FIXME
        else:
            data = {}
            for k, v in zip(args, cmd['args']):
                data[k] = v
            data.update(kwargs)

        whole_url = os.path.join(self.framework.base_url, url)
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
                    raise exc(r.json())

            raise Exception("Error code %d: %s" % (r.status_code, r.content))
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
        self.base_url = base_url
        self.api_data = api_data
        self.headers = headers

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
    def __init__(self, base_url, framework_endpoint, framework_key=None, headers=None, privileged_key=None):
        self.headers = headers or {}
        self.base_url = base_url
        self.framework_endpoint = framework_endpoint
        self.endpoints = None
        self.framework_key = framework_key
        self.privileged_key = privileged_key

    def lazy_load(self):
        if self.endpoints:
            return

        if self.base_url is None:
            raise Exception("Did not find framework matching the name '{}'".format(self.framework_key))

        these_headers = {}
        these_headers.update(self.headers)
        if self.privileged_key:
            these_headers['X-OTX-API-KEY'] = self.privileged_key
            these_headers['OTX-AUTHORIZATION-KEY'] = self.privileged_key
        # logger.warn("lazy load headers = %r", these_headers)

        url = os.path.join(self.base_url, self.framework_endpoint)
        r = session.get(url, headers=these_headers)
        if r.status_code >= 300:
            raise Exception("Status code %d encountered while trying to get framework endpoint: %r" % (r.status_code, url))
        try:
            self.endpoints = r.json()
        except Exception as e:
            raise Exception("Framework endpoint did not return data: url=%r, error=%r" % (url, e))

    def __getattr__(self, apiname):
        if apiname.startswith('_'):
            return self.__dict__.get('apiname')

        self.lazy_load()
        return Framework(self.base_url, self.headers, self.endpoints[apiname])

    def list_apis(self):
        self.lazy_load()
        return self.endpoints.keys()

    def list_endpoints(self):
        self.lazy_load()
        return {x: [foo for foo in y.keys() if not foo.startswith('_')] for x, y in self.endpoints.items()}

    @contextlib.contextmanager
    def manage_otxp_login(self, *args, **kwargs):
        oldcreds = self.headers.copy()
        self.otxp_login(*args, **kwargs)

        yield

        self.headers = oldcreds

    def otxp_login(self, username=None, password=None, key=None):
        # self.headers['Referer'] = base_url
        if key:
            self.headers['X-OTX-API-KEY'] = key
            return
        else:
            data = {'username': username, 'password': password}
            r = self.post('/auth/login', data)
            if r.status_code != 200:
                raise Exception("Failed to log into OTX with username/password: status_code={}".format(r.status_code))

            self.headers['AUTHORIZATION'] = r.json()['key']

        return self

    def otxb_login(self):
        self.headers["otx-authorization-key"] = ConfigUtils.get_value("auth-secret")
        return self


def factory(framework, privileged_key=None, headers=None):
    fw = ConfigUtils.get_value("api_frameworks")
    base_url, framework_endpoint = fw.get(framework, [None, None])
    return Frameworks(
        base_url=base_url,
        framework_endpoint=framework_endpoint,
        framework_key=framework,
        privileged_key=privileged_key,
        headers=headers,
    )


# a simple test
if __name__ == '__main__':
    frameworks = factory('osmal-ci')

    print(frameworks.list_apis())
    print(frameworks.list())
    print(frameworks.OsmalApi.list_functions())

    print(frameworks.OsmalApi.hashes(hashes=[
        '04c1416ea184f09a24c601ff1a09a4a4a5ee5fd2228cb504c8bbb15879eaa6ea',
        '7ffe5dfbc6cacb25b205d97fa953cd6b',  # good hash
        '9593137ded7e944e10edd3b75a344bea58c4819f318e90bc8fe29f450aaca8e3',  # dne
        'foo'  # bad hash
    ]))
