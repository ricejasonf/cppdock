FROM ricejasonf/emscripten_fastcomp:1.37.39

  RUN apt-get update && apt-get -yq install \
    cmake python bash-completion vim \
    && echo '. /usr/share/bash-completion/bash_completion && set -o vi' >> /root/.bashrc \
    && echo 'set hlsearch' >> /root/.vimrc \
    && mkdir /opt/install \
    && mkdir /opt/build

  RUN  ln -s /usr/local /opt/sysroot

  COPY cppdock /usr/local/bin
  COPY recipes/ /root/.cppdock_recipes
  COPY toolchain/linux_x64.cmake /opt/toolchain.cmake
