# Name the container engine command (podman or docker.)
CPPDOCK_ENGINE ?= podman

# Build the platform images with cppdock from the locks in cppdock.json.
CPPDOCK ?= ./cppdock

.PHONY: platforms cppdock platform_linux_x64 platform_emscripten boost platform_tvossimulator

cppdock:
	$(CPPDOCK) release cppdock

platforms: cppdock platform_linux_x64 platform_emscripten

platform_linux_x64:
	$(CPPDOCK) release linux_x64

platform_emscripten:
	$(CPPDOCK) release emscripten

platform_tvossimulator:
	$(CPPDOCK_ENGINE) build --force-rm=true -f ./Dockerfile-tvossimulator -t docker.io/ricejasonf/cppdock:tvossimulator .

platform_macosx:
	$(CPPDOCK_ENGINE) build --force-rm=true -f ./Dockerfile-macosx -t docker.io/ricejasonf/cppdock:macosx .

temp:
	$(CPPDOCK_ENGINE) build --force-rm=true -f ./Dockerfile-temp -t docker.io/ricejasonf/cppdock:temp .

install:
	cp ./cppdock /usr/local/bin/

push: boost
	$(CPPDOCK) release --push --no-build cppdock && \
	$(CPPDOCK) release --push --no-build linux_x64 && \
	$(CPPDOCK) release --push --no-build emscripten && \
	$(CPPDOCK_ENGINE) push docker.io/ricejasonf/boost:1_85_0 && \
	$(CPPDOCK_ENGINE) push docker.io/ricejasonf/boost_header_only:1_85_0

# Prebuild dependencies.
boost:
	$(CPPDOCK_ENGINE) buildx build . -f ./recipes_docker/Dockerfile-boost --tag docker.io/ricejasonf/boost:1_85_0 \
		--target=boost && \
	$(CPPDOCK_ENGINE) buildx build . -f ./recipes_docker/Dockerfile-boost --tag docker.io/ricejasonf/boost_header_only:1_85_0 \
		--target=boost_header_only

