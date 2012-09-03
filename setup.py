#!/usr/bin/env python

import os
import sys

import basic_oauth

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

requires = []

setup(
    name='basic_oauth',
    version=basic_oauth.__version__,
    description=('Implements the "Resource Owner Password Credentials Grant" '
        'from Oauth v2.'),
    long_description=open('README.md').read(),
    author='Sam Alba',
    author_email='sam.alba@gmail.com',
    url='http://github.com/samalba/basic_oauth',
    packages=[
        'basic_oauth'
        ],
    package_data={'': ['LICENSE']},
    package_dir={'basic_oauth': 'basic_oauth'},
    include_package_data=True,
    install_requires=requires,
    license=open('LICENSE').read(),
    classifiers=(
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python'
    )
)