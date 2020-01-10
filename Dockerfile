FROM ubuntu:eoan

RUN  apt-get update \
  && apt-get -yq install \
      python cmake git autoconf bash-completion vim wget \
  && echo '. /usr/share/bash-completion/bash_completion && set -o vi' >> /root/.bashrc \
  && echo 'set hlsearch' >> /root/.vimrc

COPY cppdock /usr/local/bin/
COPY cppdock /opt/install/bin/
COPY recipes/ /root/.cppdock_recipes
