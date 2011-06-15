#! /usr/bin/python -tt

import imp
import sys

from setuptools import setup

# Hack to import _version file without importing gh_bugs/__init__.py, its
# purpose is to allow import without requiring dependencies at this point.
ver_file = open("gh_bugs/_version.py")
_version = imp.load_module("_version", ver_file, ver_file.name,
                           (".py", ver_file.mode, imp.PY_SOURCE))

install_requires = ['argh', 'github2>=0.3.0', 'Jinja2>=2', 'Pygments']
if sys.version_info[:2] < (2, 7):
    install_requires.append('argparse')


setup(
    name='gh_bugs',
    version=_version.dotted,
    url="https://github.com/JNRowe/gh_bugs",
    author="James Rowe",
    author_email="jnrowe@gmail.com",
    classifiers=[
        'Programming Language :: Python',
    ],
    packages=['gh_bugs', ],
    include_package_data=True,
    package_data={'': ['templates/*/*.mkd', "templates/*/*.txt"], },
    entry_points={'console_scripts': ['gh_bugs = gh_bugs:main', ]},
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'colour': ['termcolor', ],
        'color': ['termcolor', ],
    },
)
