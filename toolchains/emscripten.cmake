cmake_minimum_required(VERSION 3.31)

# Use the toolchain that ships with emscripten.
include("/usr/local/emscripten/cmake/Modules/Platform/Emscripten.cmake")

# Install into the cppdock install prefix and search the platform sysroot.
set(CMAKE_INSTALL_PREFIX "/opt/install")
set(CMAKE_SYSTEM_INCLUDE_PATH "/opt/sysroot/include")
