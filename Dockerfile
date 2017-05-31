FROM ubuntu:artful
MAINTAINER Jason Rice
RUN apt-get update \
  && apt-get -yq install
      cmake git autoconf bash-completion vim \
  && echo '. /usr/share/bash-completion/bash_completion && set -o vi' >> /root/.bashrc \
  && echo 'set hlsearch' >> /root/.vimrc
