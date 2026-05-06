FROM ubuntu:25.10

RUN  apt-get update \
  && apt-get -yq install \
      python-is-python3 python3-pip cmake git autoconf \
      bash-completion vim wget xz-utils \
      libedit-dev valgrind \
  && pip install lit --break-system-packages \
  && echo '. /usr/share/bash-completion/bash_completion && set -o vi' >> /root/.bashrc \
  && echo 'HISTCONTROL=ignoreboth:erasedups' >> /root/.bashrc \
  && echo 'PS1="[\u@\h \W]\$ "' >> /root/.bashrc \
  && echo 'PS1="\[\e[0;32m\]${PS1}\[\e[m\]"' >> /root/.bashrc \
  && echo 'set hlsearch' >> /root/.vimrc

COPY cppdock /usr/local/bin/
COPY cppdock /opt/install/bin/
COPY recipes/ /opt/cppdock/recipes
COPY toolchains/ /opt/cppdock/toolchains
RUN ln -s /usr/local /opt/sysroot
