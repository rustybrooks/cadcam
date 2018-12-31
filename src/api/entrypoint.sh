#!/usr/bin/env bash

cd /srv/src

if [[ "${ENVIRONMENT}" == "prod" ]]; then
    gunicorn -b 0.0.0.0:5000 --config /srv/src/api/gunicorn.py api.api:app
else
    export FLASK_DEBUG=1
    export FLASK_APP=api.api
#    export LC_ALL=C.UTF-8
#    export LANG=C.UTF-8
    python -m flask run --host=0.0.0.0
fi

while true; do echo hi; sleep 30; done

