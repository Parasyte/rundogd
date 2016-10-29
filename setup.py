#!/usr/bin/env python

from setuptools import setup

setup(
    name='rundogd',
    version='1.0.0',
    description='A filesystem watcher-restarter daemon.',
    author='Jay Oster',
    author_email='jay@kodewerx.org',
    url='https://github.com/parasyte/rundogd',
    py_modules=[ 'rundogd' ],
    entry_points={
        'console_scripts': [ 'rundogd = rundogd:main' ],
    },
    install_requires=[ 'watchdog (==0.8.3)' ],
)
