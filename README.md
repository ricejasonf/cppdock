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

A docker dep is locked to `layers:sha256:<hex>`, a hash of its layers, when the image has a `layers-sha256-<hex>` tag (`cppdock release` adds one), and to its manifest digest `sha256:<hex>` otherwise.

The platform's base image is locked the same way, in `base_image_revision`. Set it to `""` to leave the base image unlocked. Every image a generated build uses is made local before the build, so the build never pulls.

### Platform Images

A platform of type `image` builds a Dockerfile, and `cppdock release` tags the result with its `push_tag` and its layers tag. Its deps are docker deps, and each one is passed to the Dockerfile as the build arg its `build_arg` names, so each `FROM` names a locked image:

```json
"linux_x64": {
  "type": "image",
  "dockerfile": "Dockerfile-linux_x64",
  "push_tag": "ricejasonf/cppdock:linux_x64",
  "deps": [
    [
      {
        "name": "ricejasonf/cppdock",
        "type": "docker",
        "build_arg": "CPPDOCK",
        "revision": "layers:sha256:430d584fb88f..."
      }
    ]
  ]
}
```

The `cppdock.json` in this repo builds the `cppdock`, `linux_x64` and `emscripten` images this way. After rebuilding one of them, delete the `revision` of the dep that names it in the next image and run `cppdock init` to relock it. `cppdock release --push --no-build` pushes an image that was already released without building it again, as `make push` does.

### Local Overrides

A `cppdock-local.json` beside `cppdock.json` overrides it on this machine only. Keep it out of version control. It is merged after locking and is never written back, so `cppdock.json` keeps its locks.

- Top-level sections (such as `cppdock`) are merged by key.
- A platform's options are overridden by key.
- A platform's `deps` is a flat list. Each entry overrides, in place, the dep with the same `name`.
- A docker dep override without a `revision` uses the local image `name:tag` as it is, unverified.
- A git dep override without a `revision` is relocked to its `tag`.

For example, to build a project against a dependency you released locally:

```json
{
  "platforms": {
    "develop": {
      "deps": [{"name": "ricejasonf/schir-project"}]
    }
  }
}
```

A platform's `cmake_args` lists extra arguments for the CMake configure step of the project, such as `["-DSCHIR_ENABLE_ASSERTIONS=ON"]`. The default recipes read them from `CPPDOCK_CMAKE_ARGS`.

While a local file is present:

- Builds use a separate build volume, named with a `-local` suffix.
- `cppdock release --push` refuses to run.

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

The platform base image should have any build tools required such as CMake or Python as well as an `/opt/toolchain.cmake` if you are relying on any default CMake recipes. It also needs the builtin recipes and toolchain files in `/opt/cppdock`, as the cppdock images have. The `cppdock` script itself is not in any image: each build copies the running script into the image it generates from the base image.
