ARG EMSCRIPTEN_TAG=1.38.25
FROM ricejasonf/emscripten:$EMSCRIPTEN_TAG
  COPY cppdock /usr/local/bin
  COPY recipes/ /root/.cppdock_recipes
  COPY toolchain/emscripten.cmake /opt/toolchain.cmake

  RUN ln -s /usr/local/src/emscripten/system /opt/sysroot && mkdir /opt/install
