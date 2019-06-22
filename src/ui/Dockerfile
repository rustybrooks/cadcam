FROM ubuntu:18.04

RUN apt-get -y update \
 && apt-get -yq install curl apt-utils sudo nano build-essential \
 && curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash - \
 && apt-get install -y nodejs
 && apt-get clean \
 && rm -rf /var/cache/apt/archives/*

RUN mkdir -p /srv/src

WORKDIR /srv

COPY . /srv/src
WORKDIR /srv/src/ui/app
RUN npm install
RUN npm run build

ENTRYPOINT /srv/src/ui/entrypoint.sh
