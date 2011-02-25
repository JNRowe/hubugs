#! /usr/bin/python -tt

import sys

from setuptools import setup

from gh_bugs import __version__

setup(
    name='gh_bugs',
    version=__version__,
    classifiers=[
        'Programming Language :: Python',
    ],
    packages=['gh_bugs', ],
    include_package_data=True,
    package_data={'': ['templates/*/*.mkd', "templates/*/*.txt"], },
    entry_points={'console_scripts': ['gh_bugs = gh_bugs:main', ]},
    zip_safe=False,
    install_requires = ['github2', 'Jinja2>=2'],
)
