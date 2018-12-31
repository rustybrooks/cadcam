#!/usr/bin/env python

from flask import Flask, Response
import gevent
from gevent.wsgi import WSGIServer
import datetime
import json
import logging
import os
import signal
import sys

import api_framework

app = Flask(__name__)

api_framework.app_class_proxy(app, '', '/framework', api_framework.FrameworkApi())

@app.route("/ping")
def ping():
    response = "HI" 
    return Response(response, mimetype='text/plain')

if __name__ == '__main__':
    root = logging.getLogger()
    root.addHandler(logging.StreamHandler(sys.stderr))
    root.setLevel(logging.INFO)
    log = logging.getLogger(__name__)

    port = int(os.environ.get("FLASK_PORT", "8000"))
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    log.info("RUNNING ON %s %s", host, port)
    debug = os.environ.get("FLASK_DEBUG", "False")

    # apps.register_apps(app)

    if debug == "True":
        log.info("Starting dev server")
        app.debug = True
        app.run(host=host, port=port)
    else:
        # setup_handler(logger=root)
        timeout = os.environ.get("SHUTDOWN_TIMEOUT", "30")
        http_server = WSGIServer((host, port), app)

        def shutdown(*args):
            log.info("Shutting down with timeout {0}".format(timeout))
            http_server.stop(timeout=int(timeout))

        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGQUIT, shutdown)
        signal.signal(signal.SIGINT, shutdown)

        log.info("Starting in gevent")
        http_server.serve_forever()

