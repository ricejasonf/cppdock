FROM ricejasonf/emscripten:1.37.39 AS cctools

  # cctools (linker for darwin targets)
  RUN git clone https://github.com/tpoechtrager/cctools-port.git \
    && cd cctools-port/cctools \
    && ./configure --prefix /opt/install \
    && make \
    && make install
 
FROM ricejasonf/emscripten:1.37.19

  RUN apt-get update && apt-get -yq install \
    cmake python bash-completion vim patch clang libxml2-devel \
    && echo '. /usr/share/bash-completion/bash_completion && set -o vi' >> /root/.bashrc \
    && echo 'set hlsearch' >> /root/.vimrc

  COPY cppdock /usr/local/bin
  COPY recipes/ /root/.cppdock_recipes
  COPY ./toolchain/macosx.cmake /opt/toolchain.cmake
  COPY --from=cctools /opt/install /usr/local
