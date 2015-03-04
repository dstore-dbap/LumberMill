#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2014 Björn Puttmann

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys

from gambolputty import __version__, __app_name__, __author__, __email__, __url__

try:
    from setuptools import setup
    setup  # workaround for pyflakes issue #13
except ImportError:
    from distutils.core import setup

try:
    import __pypy__
    is_pypy = True
except ImportError:
    is_pypy = False

requirements = open('requirements/requirements.txt').readlines()
if is_pypy:
    requirements.extend(open('requirements/requirements-pypy.txt').readlines())

setup(
    name=__app_name__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    packages=['gambolputty'],
    url=__url__,
    license='LICENSE',
    classifiers=[
        'Intended Audience :: System Administrators',
        'License :: Apache License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: pypy',
        'Topic :: System :: Logging',
    ],
    description='',
    long_description=open('README.rst').read() + '\n\n',
    tests_require=open('requirements/requirements-test.txt').readlines(),
    test_suite='nose.collector',
    install_requires=requirements, requires=['six']
)