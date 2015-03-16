#!/bin/env python
from paver.easy import needs, path, sh
from paver.tasks import task

PKGNAME = 'tomate'

ROOT_PATH = path(__file__).dirname().abspath()

DATA_PATH = ROOT_PATH / 'data'

TOMATE_PATH = ROOT_PATH / 'tomate'


@needs(['run'])
@task
def default():
    pass


@needs('clean')
@task
def run():
    import os
    import sys
    from xdg.BaseDirectory import xdg_data_dirs

    xdg_data_dirs.insert(0, str(DATA_PATH))
    os.environ['XDG_DATA_DIRS'] = ':'.join(xdg_data_dirs)
    os.environ['LIBOVERLAY_SCROLLBAR'] = '0'

    sys.path.insert(0, str(TOMATE_PATH))
    sys.path.insert(0, str(ROOT_PATH))
    sys.argv = ['/usr/bin/paver', '-v']

    from tomate_gtk.main import main
    main()


@task
def test():
    import os
    from xdg.BaseDirectory import xdg_data_dirs

    xdg_data_dirs.insert(0, str(DATA_PATH))
    os.environ['XDG_DATA_DIRS'] = ':'.join(xdg_data_dirs)
    os.environ['LIBOVERLAY_SCROLLBAR'] = '0'
    os.environ['PYTHONPATH'] = '%s:%s' % (TOMATE_PATH, ROOT_PATH)

    sh('xvfb-run -a nosetests')


@task
def clean():
    sh('pyclean tomate_gtk')


@needs(['docker_rmi', 'docker_build'])
@task
def docker_test():
    sh('docker run --rm -v $PWD:/code eliostvs/tomate-gtk test')


@task
def docker_rmi():
    sh('docker rmi eliostvs/tomate-gtk', ignore_error=True)


@task
def docker_build():
    sh('docker build -t eliostvs/tomate-gtk .')


@task
def docker_run():
    sh('docker run --rm -v $PWD:/code -e DISPLAY --net=host '
       '-v $HOME/.Xauthority:/root/.Xauthority eliostvs/tomate-gtk')
