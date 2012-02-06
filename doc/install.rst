Installation
------------

You can install :mod:`hubugs` either via :abbr:`PyPI (Python Package Index)` or
from source.

Using :abbr:`PyPI (Python Package Index)`
'''''''''''''''''''''''''''''''''''''''''

To install using :pypi:`pip`::

    $ pip install hubugs  # to install in Python's site-packages
    $ pip install --install-option="--user" hubugs  # to install for a single user

To install using :pypi:`easy_install <setuptools>`::

    $ easy_install hubugs

From source
'''''''''''

If you have downloaded a source tarball you can install it with the following
steps::

    $ python setup.py build
    # python setup.py install  # to install in Python's site-packages
    $ python setup.py install --user  # to install for a single user

:mod:`hubugs` depends on following packages, all of which are available from
:abbr:`PyPI (Python Package Index)`:

* :pypi:`argh` an excellent package for building command line tools in Python
* :pypi:`blessings` for terminal formatting including colourisation
* :pypi:`github2` for wrapping access to the GitHub API
* :pypi:`html2text` is used formatting HTML for the terminal
* :pypi:`Jinja2` for templating
* :pypi:`misaka` is used for converting issue text to HTML
* :pypi:`Pygments` for syntax highlighting in template output
