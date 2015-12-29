PROJECT = tomate-gtk
AUTHOR = eliostvs
PROJECT_ROOT = $(CURDIR)
PACKAGE_NAME = tomate_gtk
DOCKER_IMAGE_NAME= $(AUTHOR)/$(PROJECT)
DATA_PATH = $(PROJECT_ROOT)/data
DOCKER_IMAGE_NAME= $(AUTHOR)/$(PROJECT)
TOMATE_PATH = $(PROJECT_ROOT)/tomate
XDG_DATA_DIRS = XDG_DATA_DIRS=$(DATA_PATH):/home/$(USER)/.local/share:/usr/local/share:/usr/share
PYTHONPATH = PYTHONPATH=$(TOMATE_PATH):$(PROJECT_ROOT)
VERBOSITY=1

clean:
	find . \( -iname "*.pyc" -o -iname "__pycache__" \) -print0 | xargs -0 rm -rf

run:
	$(XDG_DATA_DIRS) $(PYTHONPATH) python -m $(PACKAGE_NAME) -v

test: clean
	$(XDG_DATA_DIRS) $(PYTHONPATH) xvfb-run -a nosetests --with-coverage --cover-erase --cover-package=$(PACKAGE_NAME)

docker-run:
	docker run --rm -it -e DISPLAY --net=host \
	-v $(PROJECT_ROOT):/code \
	-v $(HOME)/.Xauthority:/root/.Xauthority \
	$(DOCKER_IMAGE_NAME) run

docker-clean:
	docker rmi $(DOCKER_IMAGE_NAME) 2> /dev/null || echo $(DOCKER_IMAGE_NAME) not found!

docker-build:
	docker build -t $(DOCKER_IMAGE_NAME) .

docker-test:
	docker run --rm -it -v $(PROJECT_ROOT):/code $(DOCKER_IMAGE_NAME)

docker-all: docker-clean docker-build docker-test

docker-enter:
	docker run --rm -v $(PROJECT_ROOT):/code -it --entrypoint="bash" $(DOCKER_IMAGE_NAME)
