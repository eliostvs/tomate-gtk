#!/bin/env python

from paver.easy import needs, path, sh
from paver.setuputils import install_distutils_tasks
from paver.tasks import task

install_distutils_tasks()

PKGNAME = 'tomate'

ROOT_PATH = path(__file__).dirname().abspath()

DATA_PATH = ROOT_PATH / 'data'

TOMATE_PATH = ROOT_PATH / 'tomate'


@needs(['test'])
@task
def default():
    pass


@task
@needs(['clean', 'setup'])
def test(options):
    sh('nosetests tests')


@task
def clear():
    sh('pyclean tomate_gtk')


@needs(['clean', 'setup'])
@task
def run():
    sh('python -m tomate_gtk -v')


@task
def setup():
    import os
    from xdg.BaseDirectory import xdg_data_dirs

    xdg_data_dirs.insert(0, str(DATA_PATH))

    os.environ['XDG_DATA_DIRS'] = ':'.join(xdg_data_dirs)
    os.environ['LIBOVERLAY_SCROLLBAR'] = '0'
    os.environ['PYTHONPATH'] = '%s:%s' % (TOMATE_PATH, ROOT_PATH)


@task
def docker_build():
    sh('docker build -t eliostvs/tomate-gtk .')


@task
def docker_run():
    sh('docker run --rm -v $PWD:/code -e DISPLAY --net=host '
       '-v $HOME/.Xauthority:/root/.Xauthority eliostvs/tomate-gtk')
