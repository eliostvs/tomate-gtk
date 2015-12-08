PROJECT = tomate-gtk
AUTHOR = eliostvs
PROJECT_ROOT = $(CURDIR)
PACKAGE_NAME = tomate_gtk
DOCKER_IMAGE_NAME= $(AUTHOR)/$(PROJECT)
VERBOSITY=1
DATA_PATH = $(PROJECT_ROOT)/data
DOCKER_IMAGE_NAME= $(AUTHOR)/$(PROJECT)
TOMATE_PATH = $(PROJECT_ROOT)/tomate
XDG_DATA_DIRS = XDG_DATA_DIRS=$(DATA_PATH):/home/$(USER)/.local/share:/usr/local/share:/usr/share
PYTHONPATH = PYTHONPATH=$(TOMATE_PATH):$(PROJECT_ROOT)

clean:
	find . \( -iname "*.pyc" -o -iname "__pycache__" \) -print0 | xargs -0 rm -rf

run:
	$(XDG_DATA_DIRS) $(PYTHONPATH) python -m $(PACKAGE_NAME) -v

test: clean
	$(XDG_DATA_DIRS) $(PYTHONPATH) nosetests --verbosity=$(VERBOSITY)

docker-test:
	docker run --rm -v $PWD:/code $(DOCKER_IMAGE_NAME) test

docker-clean:
	docker rmi $(DOCKER_IMAGE_NAME) 2> /dev/null || echo $(DOCKER_IMAGE_NAME) not found!

docker-build:
	docker build -t $(DOCKER_IMAGE_NAME) .

docker-all: docker-clean docker-build docker-test

docker-run:
	docker run --rm -it -v $(PROJECT_ROOT):/code -e DISPLAY --net=host \
    -v $(HOME)/.Xauthority:/root/.Xauthority $(DOCKER_IMAGE_NAME)

docker-enter:
	docker run --rm -v $(PROJECT_ROOT):/code -it --entrypoint="bash" $(DOCKER_IMAGE_NAME)
