PACKAGE = tomate-gtk
AUTHOR = eliostvs
PACKAGE_ROOT = $(CURDIR)
PACKAGE_DIR = tomate_gtk
DOCKER_IMAGE_NAME= $(AUTHOR)/$(PACKAGE)
DATA_PATH = $(PACKAGE_ROOT)/data
TOMATE_PATH = $(PACKAGE_ROOT)/tomate
XDG_DATA_DIRS = XDG_DATA_DIRS=$(DATA_PATH):/home/$(USER)/.local/share:/usr/local/share:/usr/share
PYTHONPATH=PYTHONPATH=$(TOMATE_PATH):$(PACKAGE_ROOT)
PROJECT = home:eliostvs:tomate
OBS_API_URL = https://api.opensuse.org:443/trigger/runservice?project=$(PROJECT)&package=$(PACKAGE)

submodule:
	git submodule init
	git submodule update

clean:
	find . \( -iname "*.pyc" -o -iname "__pycache__" \) -print0 | xargs -0 rm -rf

run:
	$(XDG_DATA_DIRS) $(PYTHONPATH) python -m $(PACKAGE_DIR) -v

test: clean
	$(XDG_DATA_DIRS) $(PYTHONPATH) xvfb-run -a py.test -v \
	    --cov-report term-missing --cov=$(PACKAGE_DIR) \
	    --flake8

docker-run:
	docker run --rm -it -e DISPLAY --net=host \
	-v $(PACKAGE_ROOT):/code \
	-v $(HOME)/.Xauthority:/root/.Xauthority \
	$(DOCKER_IMAGE_NAME) run

docker-clean:
	docker rmi $(DOCKER_IMAGE_NAME) 2> /dev/null || echo $(DOCKER_IMAGE_NAME) not found!

docker-build:
	docker build -t $(DOCKER_IMAGE_NAME) .

docker-test:
	docker run --rm -it -v $(PACKAGE_ROOT):/code $(DOCKER_IMAGE_NAME)

docker-all: docker-clean docker-build docker-test

docker-enter:
	docker run --rm -v $(PACKAGE_ROOT):/code -it --entrypoint="bash" $(DOCKER_IMAGE_NAME)
