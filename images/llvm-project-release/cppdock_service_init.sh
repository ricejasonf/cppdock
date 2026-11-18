#!/bin/bash

BUILD_TYPE=${BUILD_TYPE:-release}
TARGET=${TARGET:-install}
NPROC=${NPROC:-$(nproc)}

echo "Check llvm-project build initialization"
if [ ! -f "CMakeCache.txt" ]; then
  echo "Initializing llvm-project build"
  cmake \
    -DCMAKE_BUILD_TYPE=$BUILD_TYPE \
    -DCMAKE_INSTALL_PREFIX=/opt/install \
    -DCMAKE_TOOLCHAIN_FILE=/opt/toolchain.cmake \
    -DLLVM_TARGETS_TO_BUILD="WebAssembly;X86;" \
    -DLLVM_ENABLE_RUNTIMES="libcxx;libcxxabi;libunwind" \
    -DLLVM_RUNTIME_TARGETS="x86_64-unknown-linux-gnu" \
    -DLLVM_ENABLE_PROJECTS="mlir;clang;lld;lldb;clang-tools-extra" \
    -DLLVM_LINK_LLVM_DYLIB=ON \
    -DLLVM_BUILD_LLVM_DYLIB=ON \
    -DLLVM_INSTALL_UTILS=ON \
    -DLLVM_INCLUDE_EXAMPLES=OFF -DLLVM_INCLUDE_TESTS=OFF \
    -DCLANG_INCLUDE_TESTS=OFF \
    -DLLDB_ENABLE_LIBEDIT=ON \
    /opt/src/llvm
fi

# INIT_ONLY is used for allowing a shell environment
# initiated by cppdock
if [ -z "$INIT_ONLY" ]; then
  echo "Building llvm-project target: $TARGET"
  cmake --build . --target $TARGET -- -j$NPROC
else
  echo "Skipping llvm-project build target"
fi

