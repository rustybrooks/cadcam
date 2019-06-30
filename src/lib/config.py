import json
import logging
import os


logger = logging.getLogger(__name__)


def get_config():
    config_file = os.path.join('/srv/data/cadcam.cfg')
    if os.path.exists(config_file):
        return json.load(open(config_file))

    return {}


def get_config_key(key):
    conf = get_config()
    eval = os.getenv(key, None)
    cval = conf.get(key)
    return eval or cval


