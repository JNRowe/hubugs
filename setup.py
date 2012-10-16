#! /usr/bin/python -tt

import sys

from setuptools import setup

# Hack to import _version file without importing hubugs/__init__.py, its
# purpose is to allow import without requiring dependencies at this point.
_version = {}
execfile('hubugs/_version.py', {}, _version)

install_requires = ['argh', 'blessings', 'html2text', 'httplib2>=0.7.4',
                    'Jinja2>=2', 'kitchen', 'Pygments', 'schematics']
if sys.version_info[:2] < (2, 7):
    install_requires.append('argparse')


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
