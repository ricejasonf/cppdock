# Name the container engine command (podman or docker.)
CPPDOCK_ENGINE ?= podman

.PHONY: platforms cppdock platform_linux_x64 platform_emscripten boost platform_tvossimulator

cppdock:
	$(CPPDOCK_ENGINE) build --force-rm=true -t docker.io/ricejasonf/cppdock .

platforms: cppdock platform_linux_x64 platform_emscripten

platform_linux_x64: cppdock
	$(CPPDOCK_ENGINE) build --force-rm=true -f ./Dockerfile-linux_x64 -t docker.io/ricejasonf/cppdock:linux_x64 .

platform_emscripten: platform_linux_x64
	$(CPPDOCK_ENGINE) build --force-rm=true -f ./Dockerfile-emscripten -t docker.io/ricejasonf/cppdock:emscripten .

platform_tvossimulator:
	$(CPPDOCK_ENGINE) build --force-rm=true -f ./Dockerfile-tvossimulator -t docker.io/ricejasonf/cppdock:tvossimulator .

platform_macosx:
	$(CPPDOCK_ENGINE) build --force-rm=true -f ./Dockerfile-macosx -t docker.io/ricejasonf/cppdock:macosx .

temp:
	$(CPPDOCK_ENGINE) build --force-rm=true -f ./Dockerfile-temp -t docker.io/ricejasonf/cppdock:temp .

install:
	cp ./cppdock /usr/local/bin/

push: cppdock platforms boost
	$(CPPDOCK_ENGINE) push docker.io/ricejasonf/cppdock && \
	$(CPPDOCK_ENGINE) push docker.io/ricejasonf/cppdock:linux_x64 && \
	$(CPPDOCK_ENGINE) push docker.io/ricejasonf/cppdock:emscripten && \
	$(CPPDOCK_ENGINE) push docker.io/ricejasonf/boost:1_85_0 && \
	$(CPPDOCK_ENGINE) push docker.io/ricejasonf/boost_header_only:1_85_0

# Prebuild dependencies.
boost:
	$(CPPDOCK_ENGINE) buildx build . -f ./recipes_docker/Dockerfile-boost --tag docker.io/ricejasonf/boost:1_85_0 \
		--target=boost && \
	$(CPPDOCK_ENGINE) buildx build . -f ./recipes_docker/Dockerfile-boost --tag docker.io/ricejasonf/boost_header_only:1_85_0 \
		--target=boost_header_only

