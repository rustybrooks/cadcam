FROM ubuntu:18.04

RUN DEBIAN_FRONTEND=noninteractive apt-get -yq update \
  && DEBIAN_FRONTEND=noninteractive apt-get -yq install \
     sudo nano \
     build-essential \
     python2.7 python2.7-dev  python-tk python-pip \
     unzip cmake git libgomp1 \
     libboost-all-dev doxygen \
     libvtk6.3 libvtk6-dev python-vtk6 \
     graphviz libqd-dev libfreetype6-dev \
     libgeos-dev  libffi-dev python-cffi \
  && apt-get clean \
  && rm -rf /var/cache/apt/archives/*

RUN mkdir -p /srv/src 

WORKDIR /tmp
RUN git clone https://github.com/aewallin/opencamlib.git && mkdir opencamlib/build && cd opencamlib/build && cmake ../src && make install && rm -rf /tmp/opencamlib
RUN git clone https://github.com/aewallin/openvoronoi.git && mkdir openvoronoi/build && cd openvoronoi/build && cmake ../src && make install && rm -rf /tmp/openvoronoi
RUN git clone https://github.com/aewallin/truetype-tracer.git && mkdir truetype-tracer/build && cd truetype-tracer/build && cmake ../src && make install && rm -rf /tmp/truetype-tracer

WORKDIR /srv
ENTRYPOINT ["bash"]

COPY requirements.txt /srv/src
RUN pip install setuptools==9.1 \
  && pip install -r /srv/src/requirements.txt


