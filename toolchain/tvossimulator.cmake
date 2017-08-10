set(CMAKE_INSTALL_PREFIX /opt/sysroot)
set(CMAKE_SYSROOT /opt/sysroot)
set(CMAKE_SYSTEM_NAME Darwin)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

set(triple x86_64-apple-tvossimulator)

set(CMAKE_C_COMPILER clang)
set(CMAKE_C_COMPILER_TARGET ${triple})
set(CMAKE_CXX_COMPILER clang++)
set(CMAKE_CXX_COMPILER_TARGET ${triple})

set(CMAKE_EXE_LINKER_FLAGS "-mtvos-version-min=9.2")

set(CMAKE_AR /usr/local/bin/ar CACHE FILEPATH "Archiver")
set(CMAKE_STRIP /usr/local/bin/strip CACHE FILEPATH "Archiver")

set(CMAKE_C_COMPILER_WORKS 1)
set(CMAKE_CXX_COMPILER_WORKS 1)

# pthreads
set(CMAKE_THREAD_LIBS_INIT "-lpthread")
set(CMAKE_HAVE_THREADS_LIBRARY 1)
set(CMAKE_USE_WIN32_THREADS_INIT 0)
set(CMAKE_USE_PTHREADS_INIT 1)
