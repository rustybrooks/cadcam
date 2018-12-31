FROM rustybrooks/cadcam-base

RUN apt-get -y update \
 && mkdir /srv/logs && mkdir /var/log/gunicorn

COPY . /srv/src

RUN pip install -r $CNCHOME/requirements_api.txt

ENTRYPOINT ["/srv/src/api/entrypoint.sh"]

