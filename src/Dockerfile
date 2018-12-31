FROM ubuntu:16.04

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

RUN mkdir -p /srv/src 

WORKDIR /tmp
RUN git clone https://github.com/aewallin/opencamlib.git && mkdir opencamlib/build && cd opencamlib/build && cmake ../src && make install && rm -rf /tmp/opencamlib
RUN git clone https://github.com/aewallin/openvoronoi.git && mkdir openvoronoi/build && cd openvoronoi/build && cmake ../src && make install && rm -rf /tmp/openvoronoi
RUN git clone https://github.com/aewallin/truetype-tracer.git && mkdir truetype-tracer/build && cd truetype-tracer/build && cmake ../src && make install && rm -rf /tmp/truetype-tracer

COPY . /srv/src
RUN pip install setuptools==9.1 \
  && pip install -r /srv/src/requirements.txt

WORKDIR /srv

ENTRYPOINT ["bash"]

