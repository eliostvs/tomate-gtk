#!/bin/env python
import os

from setuptools import find_packages, setup


def find_xdg_data_files(syspath, relativepath, pkgname, data_files=[]):
    for (dirname, _, filenames) in os.walk(relativepath):
        if filenames:
            syspath = syspath.format(pkgname=pkgname)

            subpath = dirname.split(relativepath)[1]
            if subpath.startswith('/'):
                subpath = subpath[1:]

            files = [os.path.join(dirname, f) for f in filenames]

            data_files.append((os.path.join(syspath, subpath), files))

    return data_files


def find_data_files(data_map, pkgname):
    data_files = []

    for (syspath, relativepath) in data_map:
        find_xdg_data_files(syspath, relativepath, pkgname, data_files)

    return data_files


DATA_FILES = [
    ('share/icons', 'data/icons'),
    ('share/applications', 'data/applications'),
]


setup(
    author='Elio Esteves Duarte',
    author_email='elio.esteves.duarte@gmail.com',
    description='Tomate Pomodoro timer (GTK+ Interface).',
    include_package_data=True,
    keywords='pomodoro,tomate',
    license='GPL-3',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    name='tomate-gtk',
    packages=find_packages(exclude=['tomate', 'tests']),
    data_files=find_data_files(DATA_FILES, 'tomate-gtk'),
    url='https://github.com/eliostvs/tomate-gtk',
    version='0.8.0',
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'tomate-gtk=tomate_gtk.__main__:main',
        ],
    },
)
