.DELETE_ON_ERROR:
.ONESHELL:
.SHELLFLAGS   := -eu -o pipefail -c
.SILENT:
MAKEFLAGS     += --no-builtin-rules
MAKEFLAGS     += --warn-undefined-variables
SHELL         = bash

ifeq ($(origin .RECIPEPREFIX), undefined)
	$(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif
  
DATAPATH     = $(CURDIR)/tests/data
DOCKER_IMAGE = eliostvs/$(PACKAGE)
OBS_API_URL  = https://api.opensuse.org/trigger/runservice
PACKAGE      = tomate
PYTHON       ?= python
PYTHONPATH   = PYTHONPATH=$(CURDIR)
VERSION      = `cat .bumpversion.cfg | grep current_version | awk '{print $$3}'`
WORKDIR      = /code
XDGPATH      = XDG_CONFIG_HOME=$(DATAPATH) XDG_DATA_HOME=$(DATAPATH) XDG_DATA_DIRS=$(DATAPATH)

ifeq ($(shell which xvfb-run 1> /dev/null && echo yes),yes)
	ARGS = xvfb-run -a
else
	ARGS ?=
endif

.PHONY: format
format:
	black $(PACKAGE) tests/

.PHONY: clean
clean:
	find . \( -iname "*.pyc" -o -iname "__pycache__" \) -print0 | xargs -0 rm -rf
	rm -rf .eggs *.egg-info/ .coverage build/ .cache

.PHONY: test
test: clean
	echo "$(XDGPATH) $(PYTHONPATH) $(ARGS) pytest $(PYTEST) -v --cov=$(PACKAGE)"
	$(XDGPATH) $(PYTHONPATH) $(ARGS) pytest $(PYTEST) -v --cov=$(PACKAGE)

.PHONY: run
run:
	$(XDGPATH) $(PYTHONPATH) TOMATE_DEBUG=true $(PYTHON) -m $(PACKAGE) -v

release-%:
	git flow init -d
	@grep -q '\[Unreleased\]' CHANGELOG.md || (echo 'Create the [Unreleased] section in the changelog first!' && exit)
	bumpversion --verbose --commit $*
	git flow release start $(VERSION)
	GIT_MERGE_AUTOEDIT=no git flow release finish -m "Merge branch release/$(VERSION)" -T $(VERSION) $(VERSION) -p

.PHONY: trigger-build
trigger-build:
	curl -X POST -H "Authorization: Token $(TOKEN)" $(OBS_API_URL)

.PHONY: docker-run
docker-run:
	docker run --rm -it -e DISPLAY --net=host \
	-v $(CURDIR):/code \
	-v $(HOME)/.Xauthority:/root/.Xauthority \
	$(DOCKER_IMAGE) run

.PHONY: docker-clean
docker-clean:
	docker rmi $(DOCKER_IMAGE) 2> /dev/null || echo $(DOCKER_IMAGE) not found!

.PHONY: docker-test
docker-test:
	docker run --rm -it -v $(CURDIR):$(WORKDIR) --workdir $(WORKDIR) $(DOCKER_IMAGE)

.PHONY: docker-pull
docker-pull:
	docker pull $(DOCKER_IMAGE)

.PHONY: docker-all
docker-all: docker-pull docker-clean docker-test

.PHONY: docker-enter
docker-enter:
	docker run --rm -v $(CURDIR):$(WORKDIR) -it --workdir $(WORKDIR) --entrypoint="bash" $(DOCKER_IMAGE)