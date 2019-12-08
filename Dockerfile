FROM ubuntu:16.04

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade
RUN apt-get install -y --no-install-recommends --fix-missing\
  sudo \
  autoconf \
  automake \
  bison \
  build-essential \
  ca-certificates \
  cmake \
  cpp \
  curl \
  flex \
  git \
  libboost-dev \
  libboost-filesystem-dev \
  libboost-iostreams1.58-dev \
  libboost-program-options-dev \
  libboost-system-dev \
  libboost-test-dev \
  libboost-thread-dev \
  libc6-dev \
  libevent-dev \
  libffi-dev \
  libfl-dev \
  libgc-dev \
  libgc1c2 \
  libgflags-dev \
  libgmp-dev \
  libgmp10 \
  libgmpxx4ldbl \
  libjudy-dev \
  libpcap-dev \
  libreadline6 \
  libreadline6-dev \
  libssl-dev \
  libtool \
  linux-headers-$(uname -r)\
  make \
  mktemp \
  pkg-config \
  python \
  python-dev \
  python-ipaddr \
  python-pip \
  python-psutil \
  python-scapy \
  python-setuptools \
  tcpdump \
  unzip \
  wget \
  xcscope-el

WORKDIR /usr/src
RUN git clone git://github.com/mininet/mininet mininet && sudo ./mininet/util/install.sh -nwv
RUN git clone https://github.com/google/protobuf.git && \
    cd protobuf && \
    git checkout "v3.2.0" && \
    ./autogen.sh && \
    ./configure --prefix=/usr && \
    make && sudo make install && sudo ldconfig && \
    cd python && sudo python setup.py install

RUN git clone https://github.com/grpc/grpc.git && \
    cd grpc && \
    git checkout "v1.3.2" && \
    git submodule update --init --recursive && \
    make && \
    sudo make install && \
    sudo ldconfig && \
    sudo pip install grpcio

RUN git clone https://github.com/p4lang/behavioral-model.git && \
    cd behavioral-model && \
    git checkout "b447ac4c0cfd83e5e72a3cc6120251c1e91128ab" && \
    tmpdir=`mktemp -d -p .` && \
    cd ${tmpdir} && \
    bash ../travis/install-thrift.sh && \
    bash ../travis/install-nanomsg.sh && \
    sudo ldconfig && \
    bash ../travis/install-nnpy.sh && \
    cd .. && \
    sudo rm -rf $tmpdir


# --- PI/P4Runtime --- #
RUN git clone https://github.com/p4lang/PI.git && \
    cd PI && \
    git checkout "41358da0ff32c94fa13179b9cee0ab597c9ccbcc" && \
    git submodule update --init --recursive && \
    ./autogen.sh && \
    ./configure --with-proto && \
    make && \
    sudo make install && \
    sudo ldconfig


# --- Bmv2 --- #
RUN cd behavioral-model && \
    ./autogen.sh && \
    ./configure --enable-debugger --with-pi && \
    make && \
    sudo make install && \
    sudo ldconfig && \
    cd targets/simple_switch_grpc && \
    ./autogen.sh && \
    ./configure --with-thrift && \
    make && \
    sudo make install && \
    sudo ldconfig


# --- P4C --- #
RUN git clone https://github.com/p4lang/p4c && \
    cd p4c && \
    git checkout "69e132d0d663e3408d740aaf8ed534ecefc88810" && \
    git submodule update --init --recursive && \
    mkdir -p build && \
    cd build && \
    cmake .. && \
    make -j1 && \
    sudo make install && \
    sudo ldconfig

#RUN libtoolize --automake --copy --debug --force

# PDP-env deps
RUN git clone https://github.com/guodong/PDP-env /PDP-env && cd /PDP-env && pip install -r requirements.txt

CMD ["/bin/bash"]