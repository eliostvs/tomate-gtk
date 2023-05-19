ifeq ($(origin .RECIPEPREFIX), undefined)
	$(error This Make does not support .RECIPEPREFIX. Please use GNU Make 4.0 or later)
endif

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
PYTHONPATH   = PYTHONPATH=$(CURDIR):$(PLUGINPATH)
VERSION      = `cat .bumpversion.cfg | grep current_version | awk '{print $$3}'`
WORKDIR      = /code
XDGPATH      = XDG_CONFIG_HOME=$(DATAPATH) XDG_DATA_HOME=$(DATAPATH) XDG_DATA_DIRS=$(DATAPATH)

ifeq ($(shell which xvfb-run 1> /dev/null && echo yes),yes)
	ARGS = xvfb-run -a
else
	ARGS ?=
endif

.PHONY: clean
clean:
	find . \( -iname "__pycache__" \) -print0 | xargs -0 rm -rf
	rm -rf .eggs *.egg-info/ .coverage build/ .cache .pytest_cache tests/data/mime/mime.cache

.PHONY: mime
mime: clean
	update-mime-database tests/data/mime
	rm -rf tests/data/mime/{image,aliases,generic-icons,globs,globs2,icons,magic,subclasses,treemagic,types,version,XMLnamespaces}

.PHONY: format
format:
	black $(PACKAGE) tests/ $(PLUGINPATH)
	isort $(PACKAGE) tests/ $(PLUGINPATH)

.PHONY: lint
lint:
	ruff $(ARGS) $(PACKAGE) tests/

.PHONY: test
test:
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

.PHONY: docker-test
docker-test:
	docker run --rm -it -v $(CURDIR):$(WORKDIR) --workdir $(WORKDIR) $(DOCKER_IMAGE) mime test

.PHONY: docker-enter
docker-enter:
	docker run --rm -v $(CURDIR):$(WORKDIR) -it --workdir $(WORKDIR) --entrypoint="bash" $(DOCKER_IMAGE)
