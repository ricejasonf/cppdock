.PHONY: platforms cppdock platform_linux_x64 platform_emscripten boost platform_tvossimulator

cppdock:
	docker build --force-rm=true -t ricejasonf/cppdock .

platforms: platform_linux_x64 platform_emscripten

platform_linux_x64:
	docker build --force-rm=true -f ./Dockerfile-linux_x64 -t ricejasonf/cppdock:linux_x64 .

platform_emscripten:
	docker build --force-rm=true -f ./Dockerfile-emscripten -t ricejasonf/cppdock:emscripten .

platform_emscripten_1_37_19:
	docker build --force-rm=true \
		--build-arg EMSCRIPTEN_TAG=1.37.19 \
		-f ./Dockerfile-emscripten \
		-t ricejasonf/cppdock:emscripten_1_37_19 .

platform_tvossimulator:
	docker build --force-rm=true -f ./Dockerfile-tvossimulator -t ricejasonf/cppdock:tvossimulator .

platform_macosx:
	docker build --force-rm=true -f ./Dockerfile-macosx -t ricejasonf/cppdock:macosx .

temp:
	docker build --force-rm=true -f ./Dockerfile-temp -t ricejasonf/cppdock:temp .

install:
	cp ./cppdock /usr/local/bin/

push: cppdock platforms boost
	docker push ricejasonf/cppdock && \
	docker push ricejasonf/cppdock:linux_x64 && \
	docker push ricejasonf/cppdock:emscripten && \
	docker push ricejasonf/boost:1_85_0 && \
	docker push ricejasonf/boost_header_only:1_85_0

# Prebuild dependencies.
boost:
	docker buildx build . -f ./recipes_docker/Dockerfile-boost --tag ricejasonf/boost:1_85_0 \
		--target=boost && \
	docker buildx build . -f ./recipes_docker/Dockerfile-boost --tag ricejasonf/boost_header_only:1_85_0 \
		--target=boost_header_only

