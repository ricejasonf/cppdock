.PHONY: platforms cppdock linux_x64 emscripten tvossimulator

cppdock:
	docker build --force-rm=true -t ricejasonf/cppdock .

platforms: linux_x64 emscripten tvossimulator

linux_x64:
	docker build --force-rm=true -f ./Dockerfile-linux_x64 -t ricejasonf/cppdock:linux_x64 .

emscripten:
	docker build --force-rm=true -f ./Dockerfile-emscripten -t ricejasonf/cppdock:emscripten .

tvossimulator:
	docker build --force-rm=true -f ./Dockerfile-tvossimulator -t ricejasonf/cppdock:tvossimulator .
