# CppDock

>Manage and build C++ dependencies in a Docker container
>
>This project is a work in progress.

## Overview

CppDock is just a tiny python script that uses a config file to specify project specific values and platform specific dependencies.

In the simple my_app example, running `cppdock build linux_x64` will create a Docker image called `my_app_deps:linux_64`.

### Lock Library Dependencies to Specific Revisions Automatically

In a local `cppdock.ini` file you can specify repos of libraries and cppdock automatically sets the SHA of the revision so there are no unexpected changes.

```ini
[linux_x64]
ricejasonf/nbdl          =
boostorg/hana            = develop
boostorg/callable_traits = master
```

Run `cppdock init` and cppdock.ini is updated in place automatically to the current revision for that branch or tag or `HEAD`.

```ini
[linux_x64]
ricejasonf/nbdl          = 3d5f396f929b15f1b4229135686a58b4437f0967 # HEAD
boostorg/hana            = 59393cac76e718210cdf06316e1ab496ee2079eb # develop
boostorg/callable_traits = 684dfbd7dfbdd0438ef3670be10002ca33a71715 # master
```

To update a library simply delete the SHA (and `#`). Then run `cppdock init` again.

The great thing about this is that the builds for each library are cached by Docker so it only rebuilds a library when the revision has changed.

This also creates a more disciplined approach to dependency management that doesn't rely on third parties creating release tags.

### Custom Recipes

Recipes are just bash scripts that are run in a Docker container.

The default recipe assumes a typical CMake build:

```bash
#!/bin/bash

mkdir build && cd build \
&& cmake \
    -DCMAKE_TOOLCHAIN_FILE=/opt/toolchain.cmake \
    -DCMAKE_INSTALL_PREFIX=/opt/install \
    -DCMAKE_BUILD_TYPE=Release \
    .. \
&& make install
```

Custom recipes can be placed in your project's `./cppdock_recipes` directory.

Consider the following as an example describing recipe resolution.

```
./cppdock_recipes/chriskohlhoff-asio-linux_x64
./cppdock_recipes/chriskohlhoff-asio
./cppdock_recipes/default
{Then resolves using builtin recipes}
```

As you can see a platform specific recipe is the first in the order of resolution where the platform in this case is `linux_x64`.

Note that every build should install to `/opt/install`.

### Custom Compilers and SDKs

CppDock is built specifically for cross-compiling and it supports custom build environments by letting the user specify the Docker image to use for each.

Consider the following setup for a hypothetical `mydroid` platform:

```ini
[cppdock]
project = foo
platform_mydroid = mydroid_platform_image
compiler_mydroid = some_gcc_compiler

[mydroid]
kvasir-io-mpl = development
```

`mydroid_sdk` and `some_gcc_compiler` are just Docker images for the build environment and the compiler respectively.

The "platform" image should have any build tools required such as CMake or Python as well as an `/opt/toolchain.cmake` if you are relying on any default CMake recipes.

All desired artifacts other than the toolchain file must be installed to `/user/local` to be usable in the build environment.
