#!/usr/bin/env bash

cd /srv/src
pip install -U -r /srv/src/api/requirements_api.txt


while true; do
    if [[ "${ENVIRONMENT}" == "prod" ]]; then
        gunicorn -b 0.0.0.0:5000 --config /srv/src/api/gunicorn.py api.api:app
    else
        export FLASK_DEBUG=1
        export FLASK_APP=api.api
        python -m flask run --host=0.0.0.0
    fi

    sleep 30
done

