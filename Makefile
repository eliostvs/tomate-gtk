PACKAGE = tomate
AUTHOR = eliostvs
DOCKER_IMAGE_NAME= $(AUTHOR)/tomate
PACKAGE_ROOT = $(CURDIR)
PYTHONPATH = PYTHONPATH=$(PACKAGE_ROOT)
DATA_PATH = $(PACKAGE_ROOT)/data
XDG_DATA_DIRS = XDG_DATA_DIRS=$(DATA_PATH):/home/$(USER)/.local/share:/usr/local/share:/usr/share
PROJECT = home:eliostvs:tomate
OBS_API_URL = https://api.opensuse.org/trigger/runservice
DEBUG = TOMATE_DEBUG=true
WORK_DIR=/code
CURRENT_VERSION = `cat .bumpversion.cfg | grep current_version | awk '{print $$3}'`

ifeq ($(shell which xvfb-run 1> /dev/null && echo yes),yes)
	TEST_PREFIX = xvfb-run -a
else
	TEST_PREFIX =
endif

clean:
	find . \( -iname "*.pyc" -o -iname "__pycache__" \) -print0 | xargs -0 rm -rf
	rm -rf .eggs *.egg-info/ .coverage build/ .cache

test: clean
	echo "Current path: $(CURDIR)"
	$(XDG_DATA_DIRS) $(PYTHONPATH) $(TEST_PREFIX) pytest $(file) -v --cov=$(PACKAGE)

run:
	$(XDG_DATA_DIRS) $(PYTHONPATH) $(DEBUG) python -m $(PACKAGE) -v

trigger-build:
	curl -X POST -H "Authorization: Token $(TOKEN)" $(OBS_API_URL)

release-%:
	git flow init -d
	@grep -q '\[Unreleased\]' README.md || (echo 'Create the [Unreleased] section in the changelog first!' && exit)
	bumpversion --verbose --commit $*
	git flow release start $(CURRENT_VERSION)
	GIT_MERGE_AUTOEDIT=no git flow release finish -m "Merge branch release/$(CURRENT_VERSION)" -T $(CURRENT_VERSION) $(CURRENT_VERSION) -p

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
