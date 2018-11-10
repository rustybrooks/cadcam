FROM ubuntu:16.04

ENV CNCHOME=/cadcam

RUN apt-get -y update \
  && apt-get -y install \
     sudo nano \
     build-essential \
     python2.7 python2.7-dev  python-tk python-pip \
     unzip cmake git libgomp1 libglfw3-dev \
     libboost-all-dev doxygen libvtk5.10 graphviz libqd-dev libfreetype6-dev \
     libgeos-dev libglew-dev libassimp-dev libsoil-dev libvtk5-dev python-vtk \
  && apt-get clean \
  && rm -rf /var/cache/apt/archives/*

RUN mkdir -p $CNCHOME $CNCHOME/src /src $CNCHOME/src/sim $CNCHOME/src/lib
COPY ./requirements.txt $CNCHOME/requirements.txt

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

COPY ./lib/cpptk $CNCHOME/src/lib/cpptk
COPY ./lib/tcltk $CNCHOME/src/lib/tcltk

# build tcl/tk
RUN tar xvzf $CNCHOME/src/lib/tcltk/tcl8.5.18-src.tar.gz -C $CNCHOME/src/lib/tcltk/ && \
    tar xvzf $CNCHOME/src/lib/tcltk/tk8.5.18-src.tar.gz -C $CNCHOME/src/lib/tcltk/

RUN cd $CNCHOME/src/lib/tcltk/tcl8.5.18/unix && ./configure --enable-64bit --disable-shared && make install
RUN cd $CNCHOME/src/lib/tcltk/tk8.5.18/unix && ./configure --enable-64bit --disable-shared && make install

COPY ./lib/mygl $CNCHOME/src/lib/mygl
COPY ./sim/ $CNCHOME/src/sim
WORKDIR $CNCHOME/src/sim
#RUN ln -s /usr/lib/x86_64-linux-gnu/libXft.so.2 /usr/lib/x86_64-linux-gnu/libXft.so && \
#    ln -s /usr/lib/x86_64-linux-gnu/libXss.so.1 /usr/lib/x86_64-linux-gnu/libXss.so && \
#    ln -s /usr/lib/x86_64-linux-gnu/libfontconfig.so.1 /usr/lib/x86_64-linux-gnu/libfontconfig.so
RUN cd $CNCHOME/src/sim && make -f Makefile.docker

RUN pip install --upgrade pip \
  && pip install setuptools==9.1 \
  && pip install -r $CNCHOME/requirements.txt

WORKDIR /src/

ENTRYPOINT ["/bin/bash"]

