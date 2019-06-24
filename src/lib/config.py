import json
import logging
import os


logger = logging.getLogger(__name__)


def get_config():
    config_file = os.path.join('/srv/data/cadcam.cfg')
    if os.path.exists(config_file):
        return json.load(open(config_file))

    # logger.warn("config file not found: %r", config_file)
    return {}


def get_config_key(key):
    conf = get_config()
    logger.warn("config = %r", conf)
    eval = os.getenv(key, None)
    cval = conf.get(key)
    #if key == "ENVIRONMENT":
    logger.warn("key=%r eval=%r, cval=%r, val=%r", key, eval, cval, eval or cval)
    return eval or cval


