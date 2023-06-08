ifeq ($(origin .RECIPEPREFIX), undefined)
	$(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif

.DEFAULT_GOAL = help
.DELETE_ON_ERROR:
.ONESHELL:
.SHELLFLAGS   := -eu -o pipefail -c
.SILENT:
MAKEFLAGS     += --no-builtin-rules
MAKEFLAGS     += --warn-undefined-variables
SHELL         = bash

DATAPATH     = $(CURDIR)/tests/data
DOCKER_IMAGE = eliostvs/$(PACKAGE)
OBS_API_URL  = https://api.opensuse.org/trigger/runservice
PACKAGE      = tomate
PYTHON       ?= python3
PLUGINPATH   = $(CURDIR)/data/plugins
PYTEST       ?= pytest-3
PYTHONPATH   = PYTHONPATH=$(CURDIR):$(PLUGINPATH)
TESTARGS     ?=
VERSION      = `cat .bumpversion.cfg | grep current_version | awk '{print $$3}'`
WORKDIR      = /code
XDGPATH      = XDG_CONFIG_HOME=$(DATAPATH) XDG_DATA_HOME=$(DATAPATH) XDG_DATA_DIRS=$(DATAPATH)

ifeq ($(shell which xvfb-run 1> /dev/null && echo yes),yes)
	ARGS = xvfb-run -a
else
	ARGS ?=
endif


## help: print this help message
help:
	echo 'Usage:'
	sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' | sed -e 's/^/ /' | sort
.PHONY: help

## clean: clean development files
clean:
	find . \( -iname "__pycache__" \) -print0 | xargs -0 rm -rf
	rm -rf .eggs *.egg-info/ .coverage build/ .cache .pytest_cache tests/data/mime/mime.cache
.PHONY: clean

## mime: generate test mine index
mime: clean
	$(XDGPATH) update-mime-database tests/data/mime
	rm -rf tests/data/mime/{image,aliases,generic-icons,globs,globs2,icons,magic,subclasses,treemagic,types,version,XMLnamespaces}
.PHONY: mime

## format: run code formatter
format:
	black $(PACKAGE) tests/ $(PLUGINPATH)
	isort $(PACKAGE) tests/ $(PLUGINPATH)
.PHONY: format

## lint: run lint
lint:
	ruff check $(ARGS) $(PACKAGE) tests/ $(PLUGINPATH)
.PHONY: lint

## test: run tests
test:
	$(XDGPATH) $(PYTHONPATH) $(ARGS) $(PYTEST) $(TESTARGS) -v --cov=$(PACKAGE)
.PHONY: test

## run: run app locally
run:
	$(XDGPATH) $(PYTHONPATH) TOMATE_DEBUG=true $(PYTHON) -m $(PACKAGE) -v
.PHONY: run

## release-[major|minor|patch]: create release
release-%:
	git flow init -d
	@grep -q '\[Unreleased\]' CHANGELOG.md || (echo 'Create the [Unreleased] section in the changelog first!' && exit)
	bumpversion --verbose --commit $*
	git flow release start $(VERSION)
	GIT_MERGE_AUTOEDIT=no git flow release finish -m "Merge branch release/$(VERSION)" -T $(VERSION) $(VERSION) -p

## trigger-build: trigger obs build
trigger-build:
	curl -X POST -H "Authorization: Token $(TOKEN)" $(OBS_API_URL)
.PHONY: trigger-build

## docker: create docker image
docker:
	docker built -t $(DOCKER_IMAGE) .

## docker: push image to docker hub
docker-push:
	docker image push $(DOCKER_IMAGE):latest

## docker-run: run app inside
docker-run:
	docker run --rm -it -e DISPLAY --net=host \
	-v $(CURDIR):/$(WORKDIR) \
	-v $(HOME)/.Xauthority:/root/.Xauthority \
	$(DOCKER_IMAGE) run
.PHONY: docker-run

## docker-test: run tests inside docker
docker-test:
	docker run --rm -it -v $(CURDIR):$(WORKDIR) --workdir $(WORKDIR) $(DOCKER_IMAGE) mime test
.PHONY: docker-test

## docker-enter: open terminal inside docker environment
docker-enter:
	docker run --rm -v $(CURDIR):$(WORKDIR) -it --workdir $(WORKDIR) --entrypoint="bash" $(DOCKER_IMAGE)
.PHONY: docker-enter
