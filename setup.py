#! /usr/bin/python -tt
# coding=utf-8
"""setup.py - Setuptools tasks and config for hubugs"""
# Copyright © 2010, 2011, 2012, 2013  James Rowe <jnrowe@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from sys import version_info

from setuptools import setup

# Hack to import _version file without importing hubugs/__init__.py, its
# purpose is to allow import without requiring dependencies at this point.
_version = {}
execfile('hubugs/_version.py', {}, _version)

install_requires = map(str.strip, open('extra/requirements.txt').readlines())
if version_info[:2] < (2, 7):
    extra_req = map(str.strip,
                    open('extra/requirements-py26.txt').readlines()[1:])
    install_requires.extend(extra_req)

setup(
    name='hubugs',
    version=_version['dotted'],
    description="Simple client for GitHub issues",
    long_description=open("README.rst").read(),
    author="James Rowe",
    author_email="jnrowe@gmail.com",
    url="https://github.com/JNRowe/hubugs",
    license="GPL-3",
    keywords="github bugs cli",
    packages=['hubugs', ],
    include_package_data=True,
    package_data={'': ['*.crt', 'hubugs/locale/*/LC_MESSAGES/*.mo',
                       'templates/*/*.mkd', "templates/*/*.txt"], },
    entry_points={'console_scripts': ['hubugs = hubugs:main', ]},
    install_requires=install_requires,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Software Development",
        "Topic :: Software Development :: Bug Tracking",
        "Topic :: Terminals",
        "Topic :: Utilities",
    ],
)
