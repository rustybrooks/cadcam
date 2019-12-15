FROM ubuntu:18.04

RUN apt-get -y update \
 && DEBIAN_FRONTEND=noninteractive apt-get -yq install curl apt-utils sudo nano build-essential \
 && curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash - \
 && apt-get install -y nodejs \
 && apt-get clean \
 && rm -rf /var/cache/apt/archives/*

RUN mkdir -p /srv/src

ENTRYPOINT /srv/src/ui/entrypoint.sh
WORKDIR /srv/src/ui/app

## stuff that changes after here
COPY . /srv/src/
RUN npm install && npm run build && rm -rf /srv/src/ui/app/node_modules


