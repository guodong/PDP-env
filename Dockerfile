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

RUN libtoolize --automake --copy --debug --force

# PDP-env deps
RUN git clone https://github.com/guodong/PDP-env && cd PDP-env && sh install.sh && pip install -r requirements.txt

CMD ["/bin/bash"]