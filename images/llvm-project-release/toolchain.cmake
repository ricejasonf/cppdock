set(CMAKE_INSTALL_PREFIX "/opt/install")

set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)

set(CMAKE_C_COMPILER_WORKS 1)
set(CMAKE_CXX_COMPILER_WORKS 1)

set(CMAKE_CXX_FLAGS "-stdlib=libc++ --target=x86_64-unknown-linux-gnu" CACHE STRING "" FORCE)
