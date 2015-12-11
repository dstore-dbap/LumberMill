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
import os

from setuptools import find_packages
from lumbermill import __version__, __app_name__, __author__, __email__, __url__

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

# Strip comments and newlines from requirements.
parsed_requirements = []
for req in requirements:
    req = req.strip()
    if not req or req.startswith('#'):
        continue
    parsed_requirements.append(req)

setup(
    name=__app_name__,
    version=__version__,
    author=__author__,
    author_email=__email__,
    packages=find_packages(exclude=['tests']),
    url=__url__,
    #data_files=[('conf', [os.path.join('conf', _) for _ in os.listdir('conf') if _.startswith('example-')]),
    #            ('scripts', [os.path.join('scripts', _) for _ in os.listdir('scripts') if _.startswith('spam')]),
    #            ('init.d', ['scripts/etc/init.d/lumbermill'])],
    include_package_data=True,
    install_requires=parsed_requirements,
    license='LICENSE',
    classifiers=[
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: System :: Logging',
    ],
    description='A logparser with module support.',
    long_description=open('README.rst').read() + '\n\n',
    entry_points={"console_scripts": ['lumbermill = lumbermill.LumberMill:main']}
)