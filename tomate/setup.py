#!/bin/env python

from setuptools import find_packages, setup


setup(
    author='Elio Esteves Duarte',
    author_email='elio.esteves.duarte@gmail.com',
    description='A pomodoro timer. Core classes.',
    include_package_data=True,
    keywords='pomodoro',
    license='GPL-3',
    long_description=open('README.md').read(),
    name='tomate',
    packages=find_packages(exclude=['*tests']),
    url='https://github.com/eliostvs/tomate',
    version='0.2.2',
    zip_safe=False,
)
