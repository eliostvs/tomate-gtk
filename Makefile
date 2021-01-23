.SILENT:

DATAPATH     = $(CURDIR)/tests/data
DEBUG 		   = TOMATE_DEBUG=true
DOCKER_IMAGE = eliostvs/$(PACKAGE)
OBS_API_URL  = https://api.opensuse.org/trigger/runservice
PACKAGE      = tomate
PYTHON       ?= python
PYTHONPATH   = PYTHONPATH=$(CURDIR)
VERSION      = `cat .bumpversion.cfg | grep current_version | awk '{print $$3}'`
WORKDIR      = /code
XDGPATHS		 = XDG_CONFIG_HOME=$(DATAPATH) XDG_DATA_HOME=$(DATAPATH) XDG_DATA_DIRS=/usr/local/share:/usr/share

ifeq ($(shell which xvfb-run 1> /dev/null && echo yes),yes)
	ARGS = xvfb-run -a
else
	ARGS =
endif

format:
	black $(PACKAGE)

clean:
	find . \( -iname "*.pyc" -o -iname "__pycache__" \) -print0 | xargs -0 rm -rf
	rm -rf .eggs *.egg-info/ .coverage build/ .cache

test: clean
	echo "$(XDGPATHS) $(PYTHONPATH) ARGS=$(ARGS) PACKAGE=$(PACKAGE) PYTEST=$(files)"
	$(XDGPATHS) $(PYTHONPATH) $(ARGS) pytest $(PYTEST) -v --cov=$(PACKAGE)

run:
	$(XDGPATHS) $(PYTHONPATH) $(DEBUG) $(PYTHON) -m $(PACKAGE) -v

trigger-build:
	curl -X POST -H "Authorization: Token $(TOKEN)" $(OBS_API_URL)

release-%:
	git flow init -d
	@grep -q '\[Unreleased\]' CHANGELOG.md || (echo 'Create the [Unreleased] section in the changelog first!' && exit)
	bumpversion --verbose --commit $*
	git flow release start $(VERSION)
	GIT_MERGE_AUTOEDIT=no git flow release finish -m "Merge branch release/$(VERSION)" -T $(VERSION) $(VERSION) -p

docker-run:
	docker run --rm -it -e DISPLAY --net=host \
	-v $(CURDIR):/code \
	-v $(HOME)/.Xauthority:/root/.Xauthority \
	$(DOCKER_IMAGE) run

docker-clean:
	docker rmi $(DOCKER_IMAGE) 2> /dev/null || echo $(DOCKER_IMAGE) not found!

docker-test:
	docker run --rm -it -v $(CURDIR):$(WORKDIR) --workdir $(WORKDIR) $(DOCKER_IMAGE)

docker-pull:
	docker pull $(DOCKER_IMAGE)

docker-all: docker-pull docker-clean docker-test

docker-enter:
	docker run --rm -v $(CURDIR):$(WORKDIR) -it --workdir $(WORKDIR) --entrypoint="bash" $(DOCKER_IMAGE)