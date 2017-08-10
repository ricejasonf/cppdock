FROM ubuntu:artful

RUN  apt-get update \
  && apt-get -yq install \
      python cmake git autoconf bash-completion vim \
  && echo '. /usr/share/bash-completion/bash_completion && set -o vi' >> /root/.bashrc \
  && echo 'set hlsearch' >> /root/.vimrc

CMD cat
