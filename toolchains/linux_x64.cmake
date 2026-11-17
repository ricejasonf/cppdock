set(CMAKE_INSTALL_PREFIX "/opt/install")

set(CMAKE_C_COMPILER clang)
set(CMAKE_CXX_COMPILER clang++)

set(CMAKE_C_COMPILER_WORKS 1)
set(CMAKE_CXX_COMPILER_WORKS 1)

set(CMAKE_CXX_FLAGS "-stdlib=libc++ --target=x86_64-unknown-linux-gnu" CACHE STRING "" FORCE)
set(CMAKE_SYSTEM_INCLUDE_PATH "/opt/sysroot/include" CACHE STRING "" FORCE)
set(CMAKE_FIND_ROOT_PATH "/opt/sysroot" CACHE STRING "" FORCE)
#include_directories("/opt/sysroot/include/c++/v1")

# Dynamic linking stuff
set(CMAKE_EXE_LINKER_FLAGS "-Wl,--rpath=/usr/local/lib -L/usr/local/lib" CACHE STRING "" FORCE)
set(CMAKE_SHARED_LINKER_FLAGS_INIT "-L/usr/local/lib")

# pthreads
set(CMAKE_THREAD_LIBS_INIT "-lpthread")
set(CMAKE_HAVE_THREADS_LIBRARY 1)
set(CMAKE_USE_WIN32_THREADS_INIT 0)
set(CMAKE_USE_PTHREADS_INIT 1)
