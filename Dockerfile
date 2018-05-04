FROM ubuntu:bionic

RUN  apt-get update \
  && apt-get -yq install \
      python cmake git autoconf bash-completion vim \
  && echo '. /usr/share/bash-completion/bash_completion && set -o vi' >> /root/.bashrc \
  && echo 'set hlsearch' >> /root/.vimrc

COPY cppdock /usr/local/bin
COPY recipes/ /root/.cppdock_recipes

