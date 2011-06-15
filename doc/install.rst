Installation
------------

You can install :mod:`gh_bugs` either via :abbr:`PyPI (Python Package Index)` or
from source.

Using :abbr:`PyPI (Python Package Index)`
'''''''''''''''''''''''''''''''''''''''''

To install using :pypi:`pip`::

    $ pip install gh_bugs  # to install in Python's site-packages
    $ pip install --install-option="--user" gh_bugs  # to install for a single user

To install using :pypi:`easy_install <setuptools>`::

    $ easy_install gh_bugs

Optionally, :pypi:`termcolor` is required for producing coloured terminal
output.

From source
'''''''''''

If you have downloaded a source tarball you can install it with the following
steps::

    $ python setup.py build
    # python setup.py install  # to install in Python's site-packages
    $ python setup.py install --user  # to install for a single user

:mod:`gh_bugs` depends on following packages, all of which are available from
:abbr:`PyPI (Python Package Index)`:

* :pypi:`argh`, an excellent package for building command line tools in Python
* :pypi:`github2` for wrapping access to the GitHub API
* :pypi:`Jinja2` for templating
* :pypi:`Pygments` for syntax highlighting in template output

Optionally, :pypi:`termcolor` is required for producing coloured terminal
output.
