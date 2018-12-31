FROM ubuntu:16.04

ENV CNCHOME=/srv/

RUN apt-get -y update \
  && apt-get -y install \
     sudo nano \
     build-essential \
     python2.7 python2.7-dev  python-tk python-pip \
     unzip cmake git libgomp1 \
     libboost-all-dev doxygen libvtk5.10 graphviz libqd-dev libfreetype6-dev \
     libgeos-dev libvtk5-dev python-vtk \
  && apt-get clean \
  && rm -rf /var/cache/apt/archives/*

RUN mkdir -p $CNCHOME $CNCHOME/src $CNCHOME/api

WORKDIR $CNCHOME/src
RUN git clone https://github.com/aewallin/opencamlib.git
RUN git clone https://github.com/aewallin/openvoronoi.git
RUN git clone https://github.com/aewallin/truetype-tracer.git
RUN mkdir $CNCHOME/src/opencamlib/build $CNCHOME/src/openvoronoi/build $CNCHOME/src/truetype-tracer/build

# build awallin's libraries
WORKDIR $CNCHOME/src/opencamlib/build
RUN cmake ../src/ && make install
WORKDIR $CNCHOME/src/openvoronoi/build
RUN cmake ../src/ && make install
WORKDIR $CNCHOME/src/truetype-tracer/build
RUN cmake ../src/ && make install

COPY ./requirements.txt $CNCHOME/requirements.txt
RUN pip install setuptools==9.1 \
  && pip install -r $CNCHOME/requirements.txt

# COPY api/ $CNCHOME/api
# COPY python/api_framework /usr/local/lib/python2.7/dist-packages/api_framework

WORKDIR $CNCHOME

ENTRYPOINT ["bash"]

