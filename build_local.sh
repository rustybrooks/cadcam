export CNCHOME=/home/rbrooks/cadcam
echo $CNCHOME
#sudo apt-get -y update \
#  && sudo apt-get -y install \
#     sudo nano \
#     build-essential \
#     python2.7 python2.7-dev  python-tk python-pip \
#     unzip cmake git libgomp1 \
#     libboost-all-dev doxygen  graphviz libqd-dev libfreetype6-dev \
#     libgeos-dev libglew-dev libassimp-dev libsoil-dev \
#  && sudo apt-get clean 

mkdir -p $CNCHOME $CNCHOME/src $CNCHOME/src/sim $CNCHOME/src/lib
cp ./requirements.txt $CNCHOME/requirements.txt

cd $CNCHOME/src
#git clone https://github.com/aewallin/opencamlib.git
#git clone https://github.com/aewallin/openvoronoi.git
#git clone https://github.com/aewallin/truetype-tracer.git
mkdir -p $CNCHOME/src/opencamlib/build $CNCHOME/src/openvoronoi/build $CNCHOME/src/truetype-tracer/build

# build awallin's libraries
cd $CNCHOME/src/opencamlib/build
cmake ../src/ && make install
cd $CNCHOME/src/openvoronoi/build
 cmake ../src/ && make install
cd $CNCHOME/src/truetype-tracer/build
cmake ../src/ && make install
exit

cp -r ./lib/cpptk $CNCHOME/src/lib/cpptk
cp -r ./lib/tcltk $CNCHOME/src/lib/tcltk

# build tcl/tk
tar xvzf $CNCHOME/src/lib/tcltk/tcl8.5.18-src.tar.gz -C $CNCHOME/src/lib/tcltk/ && \
    tar xvzf $CNCHOME/src/lib/tcltk/tk8.5.18-src.tar.gz -C $CNCHOME/src/lib/tcltk/

cd $CNCHOME/src/lib/tcltk/tcl8.5.18/unix && ./configure --enable-64bit --disable-shared && make install
cd $CNCHOME/src/lib/tcltk/tk8.5.18/unix && ./configure --enable-64bit --disable-shared && make install

cp -r ./lib/mygl $CNCHOME/src/lib/mygl
cp -r ./sim/ $CNCHOME/src/sim
cd $CNCHOME/src/sim
#RUN ln -s /usr/lib/x86_64-linux-gnu/libXft.so.2 /usr/lib/x86_64-linux-gnu/libXft.so && \
#    ln -s /usr/lib/x86_64-linux-gnu/libXss.so.1 /usr/lib/x86_64-linux-gnu/libXss.so && \
#    ln -s /usr/lib/x86_64-linux-gnu/libfontconfig.so.1 /usr/lib/x86_64-linux-gnu/libfontconfig.so
cd $CNCHOME/src/sim && make -f Makefile.docker

pip install --upgrade pip \
  && pip install setuptools==9.1 \
  && pip install -r $CNCHOME/requirements.txt


ENTRYPOINT ["/bin/bash"]

