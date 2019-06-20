import json
import logging
import os


logger = logging.getLogger(__name__)


def get_config():
    config_file = os.path.join('/srv/data/cadcam.cfg')
    # logger.warn("config file = %r", config_file)
    if os.path.exists(config_file):
        return json.load(open(config_file))

    # logger.warn("config file not found: %r", config_file)
    return {}


def get_config_key(key):
    eval = os.getenv(key, None) 
    cval = get_config().get(key)
    #if key == "ENVIRONMENT":
    logger.warn("key=%r eval=%r, cval=%r, val=%r", key, eval, cval, eval or cval)
    return eval or cval


