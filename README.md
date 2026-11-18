# CppDock

>Manage and build C++ dependencies within a Docker container
>
>This project is a work in progress.

## Overview

CppDock is a Python script that reads a `cppdock.json` file of platforms and their locked dependencies, builds container images with those dependencies installed, and builds the project in them.

The main commands each take a platform name:

- `cppdock init` locks every dep that has no `revision` and writes the locks back to `cppdock.json`. Every other command does this too.
- `cppdock build <platform>` builds the image `<project>-<platform>-build` with the deps installed in its sysroot.
- `cppdock dev <platform>` opens a shell in that image, with the source mounted at `/opt/src` and a build volume at `/opt/build`. `--target check` builds a target instead and exits with its status.
- `cppdock release <platform>` builds the `install` target and tags an image of `/opt/install` with the platform's `push_tag` and its layers tag. `--push` pushes both.
- `cppdock clean build <platform>` removes the build volume.
- `cppdock update_source` clones the source's `repo` at its `tag` into the source `path`, or fetches the `tag` and resets a clean shallow checkout to it. It takes no platform.

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

A local file that sets only `source.path` is exempt from both, since it moves the checkout without changing what is built. `cppdock update_source` uses that path.

### LLVM Release Image

`images/llvm-project-release` builds `ricejasonf/llvm-project-release`, the LLVM fork that the `linux_x64` image installs. It builds on `linux_x64` itself, and the build takes hours.

```sh
cd images/llvm-project-release
cppdock update_source
cppdock release main --push
```

Then relock the `ricejasonf/llvm-project-release` dep of `linux_x64` in the top-level `cppdock.json`.

### Custom Recipes

Recipes are bash scripts that run in the container from `/opt/build`, with the source in `/opt/src`. Every recipe should install to `/opt/install`.

The default recipes (`recipes/default`, and `recipes/default-emscripten` for emscripten) configure the source with CMake and build `$TARGET`. The project itself is built with the platform's `service_init_script`, which is the default recipe for the `linux_x64` and `emscripten` types.

A git dep uses the first recipe found:

1. The dep's `recipe_script`, a path in the project (or in the image, if it starts with `/opt/`).
2. In `/opt/sysroot/cppdock_recipes` of the base image, then in the built-in `/opt/cppdock/recipes`, a file named after the repo and the platform name:
   - `<owner>-<repo>-<platform>`, such as `chriskohlhoff-asio-develop`
   - `<owner>-<repo>`
   - `default-<platform>`
   - `default`

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
