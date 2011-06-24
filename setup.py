#! /usr/bin/python -tt

import imp
import sys

from setuptools import setup

# Hack to import _version file without importing hubugs/__init__.py, its
# purpose is to allow import without requiring dependencies at this point.
ver_file = open("hubugs/_version.py")
_version = imp.load_module("_version", ver_file, ver_file.name,
                           (".py", ver_file.mode, imp.PY_SOURCE))

install_requires = ['argh', 'github2>=0.5.0', 'Jinja2>=2', 'Pygments']
if sys.version_info[:2] < (2, 7):
    install_requires.append('argparse')


setup(
    name='hubugs',
    version=_version.dotted,
    description="Simple client for GitHub issues",
    long_description=open("README.rst").read(),
    author="James Rowe",
    author_email="jnrowe@gmail.com",
    url="https://github.com/JNRowe/hubugs",
    license="GPL-3",
    keywords="github bugs cli",
    packages=['hubugs', ],
    include_package_data=True,
    package_data={'': ['templates/*/*.mkd', "templates/*/*.txt"], },
    entry_points={'console_scripts': ['hubugs = hubugs:main', ]},
    install_requires=install_requires,
    extras_require={
        'colour': ['termcolor', ],
        'color': ['termcolor', ],
    },
    zip_safe=False,
    test_suite="nose.collector",
    tests_require=['nose', 'mock'],
    classifiers=[
        "Development Status :: 4 - Beta",
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
