PACKAGE = tomate-gtk
AUTHOR = eliostvs
PACKAGE_ROOT = $(CURDIR)
PACKAGE_DIR = tomate_gtk
DOCKER_IMAGE_NAME= $(AUTHOR)/tomate
DATA_PATH = $(PACKAGE_ROOT)/data
TOMATE_PATH = $(PACKAGE_ROOT)/tomate
XDG_DATA_DIRS = XDG_DATA_DIRS=$(DATA_PATH):/home/$(USER)/.local/share:/usr/local/share:/usr/share
PYTHONPATH=PYTHONPATH=$(TOMATE_PATH):$(PACKAGE_ROOT)
PROJECT = home:eliostvs:tomate
OBS_API_URL = https://api.opensuse.org:443/trigger/runservice?project=$(PROJECT)&package=$(PACKAGE)
DEBUG = TOMATE_DEBUG=true
WORK_DIR=/code
CURRENT_VERSION = `cat .bumpversion.cfg | grep current_version | awk '{print $$3}'`

ifeq ($(shell which xvfb-run 1> /dev/null && echo yes),yes)
	TEST_PREFIX = xvfb-run -a
else
	TEST_PREFIX =
endif

submodule:
	git submodule init;
	git submodule update;

clean:
	find . \( -iname "*.pyc" -o -iname "__pycache__"\) -print0 | xargs -0 rm -rf

run:
	$(XDG_DATA_DIRS) $(PYTHONPATH) python -m $(PACKAGE_DIR) -v

test: clean
	$(XDG_DATA_DIRS) $(PYTHONPATH) $(DEBUG) $(TEST_PREFIX) pytest $(file) -v --cov=$(PACKAGE_DIR)

docker-run:
	docker run --rm -it -e DISPLAY --net=host \
	-v $(PACKAGE_ROOT):/code \
	-v $(HOME)/.Xauthority:/root/.Xauthority \
	$(DOCKER_IMAGE_NAME) run

docker-clean:
	docker rmi $(DOCKER_IMAGE_NAME) 2> /dev/null || echo $(DOCKER_IMAGE_NAME) not found!

docker-test:
	docker run --rm -it -v $(PACKAGE_ROOT):$(WORK_DIR) --workdir $(WORK_DIR) $(DOCKER_IMAGE_NAME)

docker-pull:
	docker pull $(DOCKER_IMAGE_NAME)

docker-all: docker-pull docker-clean docker-test

docker-enter:
	docker run --rm -v $(PACKAGE_ROOT):$(WORK_DIR) -it --workdir $(WORK_DIR) --entrypoint="bash" $(DOCKER_IMAGE_NAME)

trigger-build:
	curl -X POST -H "Authorization: Token $(TOKEN)" $(OBS_API_URL)

release-%:
	bumpversion --verbose --commit $*
	git flow release start $(CURRENT_VERSION)
	git flow release finish -p -m $(CURRENT_VERSION) $(CURRENT_VERSION)
	git push --tags
