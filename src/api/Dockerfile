FROM rustybrooks/cadcam-base

RUN apt-get -y update \
 && mkdir /srv/logs && mkdir /var/log/gunicorn

ENTRYPOINT ["/srv/src/api/entrypoint.sh"]

COPY . /srv/src
RUN pip install --no-cache-dir -r /srv/src/api/requirements_api.txt




