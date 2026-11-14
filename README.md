# CppDock

>Manage and build C++ dependencies within a Docker container
>
>This project is a work in progress.

## Overview

CppDock is just a tiny python script that uses a JSON config file to specify project specific values and platform specific dependencies based on GitHub.

In the simple `my_app` example, running `cppdock build linux_x64` will create a Docker image called `my_app_deps:linux_64`.

### Container Engine

CppDock runs `podman` by default. Set `CPPDOCK_ENGINE=docker` to use Docker instead; the `Makefile` reads the same variable.

The `dev_cluster`, `dev_registry` and `cluster_*` commands, and configs that list `machines`, rely on Docker Swarm and `docker-machine`, so they exit with an error unless the engine is `docker`.

Image names with a namespace and no registry, such as `ricejasonf/cppdock`, get the registry in `cppdock.default_registry`, which defaults to `docker.io` (so `docker.io/ricejasonf/cppdock`), with either engine. A docker dep names its registry with its own `registry` property instead of in its `name`; a dep name that starts with a registry host is an error. The swarm registry used by `dev_cluster` is `cppdock.dev_registry`.

### Lock Library Dependencies to Specific Revisions Automatically

In a local `cppdock.json` file you can specify repos of libraries and cppdock automatically sets the SHA of the revision so there are no unexpected changes.

```json
{
  "cppdock": {
    "name": "nbdl"
  },
  "platforms": {
    "develop": {
      "type": "linux_x64",
      "deps": [
        [
          {
            "name": "boostorg/callable_traits",
            "tag": "master"
          }
        ],
```

Run `cppdock init` and cppdock.json is updated in place automatically to the current revision for that branch or tag or `HEAD`.

```json
{
  "cppdock": {
    "name": "nbdl"
  },
  "platforms": {
    "develop": {
      "type": "linux_x64",
      "deps": [
        [
          {
            "name": "boostorg/callable_traits",
            "revision": "684dfbd7dfbdd0438ef3670be10002ca33a71715",
            "tag": "master"
          }
        ],
```

To update a library simply delete the "revision" property. Then run `cppdock init` again.

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

```
{
  "cppdock": {
    "name": "nbdl" /* Project name */
  },
  "platforms": {
    "develop": { /* The name of the platform */
      "type": "linux_arm", /* The type of the platform (used in recipe name) */
      "base_image": "my_droid_sdk", /* optionally specify name of docker image */
      "deps": [
        [
          {
            "name": "boostorg/callable_traits",
            "revision": "684dfbd7dfbdd0438ef3670be10002ca33a71715",
            "tag": "master"
          }
        ],
      ]
    },
  }
}
```

The platform base image should have any build tools required such as CMake or Python as well as an `/opt/toolchain.cmake` if you are relying on any default CMake recipes.
