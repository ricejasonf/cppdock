FROM ubuntu:25.10

RUN  apt-get update \
  && apt-get -yq install \
      python-is-python3 python3-pip cmake git autoconf bash-completion vim wget xz-utils \
  && pip install lit --break-system-packages \
  && echo '. /usr/share/bash-completion/bash_completion && set -o vi' >> /root/.bashrc \
  && echo 'set hlsearch' >> /root/.vimrc

COPY cppdock /usr/local/bin/
COPY cppdock /opt/install/bin/
COPY recipes/ /opt/cppdock/recipes
COPY toolchains/ /opt/cppdock/toolchains
RUN ln -s /usr/local /opt/sysroot
