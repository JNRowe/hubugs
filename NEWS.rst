User-visible changes
====================

.. contents::

0.18.0 - 2016-05-16
-------------------

* Support for httplib2_ v0.8's ``ca_certs_locater``
* Support for git's ``core.commentchar`` in templates
* Requires configobj_
* misaka_ is required [again], as GitHub no longer provide pre-formatted HTML

.. _configobj: https://pypi.python.org/pypi/configobj/

0.17.0 - 2013-02-01
-------------------

* Python 3 support!
* schematics_ is no longer required

0.16.0 - 2013-01-26
-------------------

* Support for output paging has been added
* Support for reading GitHub settings from Mercurial_ repositories
* Initial milestone support has been added, but *may* change in future releases
* ``hubugs`` requires *exactly* schematics_ v0.5
* aaargh_ is now required, and argh_ dependency has been dropped
* kitchen_ is no longer required

.. _Mercurial: http://mercurial.selenic.com/
.. _aaargh: https://pypi.python.org/pypi/aaargh/

0.15.0 - 2012-10-16
-------------------

* Search support is back!
* kitchen_ and schematics_ are now required
* Initial support for localisation, open a pull request with your translations!
* pip_ compatible requirements files can now be found in ``extra``
* nose2_ is now used for running tests
* expecter_ and nose2-cov_ are required for the test suite
* micromodels_ is no longer required, see #32

.. _kitchen: https://pypi.python.org/pypi/kitchen/
.. _schematics: https://pypi.python.org/pypi/schematics/
.. _pip: https://pypi.python.org/pypi/pip/
.. _nose2: https://pypi.python.org/pypi/nose2/
.. _expecter: https://pypi.python.org/pypi/expecter/
.. _nose2-cov: https://pypi.python.org/pypi/nose2-cov/

0.14.0 - 2012-04-30
-------------------

* Support for `GitHub API v3`_, you need to generate an access token with
  ``hubugs setup``
* Custom templates *will* require updating to work with this version
* New ``report-bug`` subcommand to report bugs you find in ``hubugs``
* The ``term_markdown`` and ``markdown`` filters have been removed
* httplib2_ is now required, but was soft dependency via `github2` before
* micromodels_ is now required
* github2_ and misaka_ are no longer required

.. _GitHub API v3: http://developer.github.com/v3/
.. _httplib2: https://pypi.python.org/pypi/httplib2
.. _micromodels: https://pypi.python.org/pypi/micromodels/

0.13.1 - 2012-02-28
-------------------

* ``github2`` v0.6.1, or newer, is required
* Support for `GitHub:Enterprise`_ using the ``--host-url`` option
* Temp files now use ``hubugs-`` prefix for easier matching in editor configs
* Basic Zsh_ completion support in ``extra/_hubugs``

.. _GitHub:Enterprise: https://enterprise.github.com/
.. _Zsh: http://www.zsh.org/

0.13.0 - 2012-02-07
-------------------

* misaka_ is now required; misaka_ supports the full range of `GitHub flavoured
  Markdown`_
* blessings_ is now required for terminal formatting

.. _misaka: https://pypi.python.org/pypi/misaka/
.. _blessings: https://pypi.python.org/pypi/blessings/
.. _GitHub flavoured Markdown: http://github.github.com/github-flavored-markdown/

0.12.0 - 2012-01-16
-------------------

* Improved Markdown using markdown2_ is available, see the ``markdown`` template
  filter for more information
* html2text_ is now required, and is available in templates using the
  ``html2text`` filter

.. _markdown2: http://github.com/trentm/python-markdown2
.. _html2text: https://pypi.python.org/pypi/html2text

0.11.0 - 2011-09-06
-------------------

* Supports opening bugs in your web browser
* ``setuptools`` users should no longer see ``UserWarning`` messages at startup

0.10.0 - 2011-06-28
-------------------

* Supports adding initial labels to bugs when opening
* Fixes for Python 2.6 compatibility

0.9.0 - 2011-06-24
------------------

* Renamed to ``hubugs``
* Thorough documentation for the package
* Testsuite that can be run via nose_ or tox_
* github2 v0.5.0, or later, is now required

.. _nose: https://pypi.python.org/pypi/nose
.. _tox: https://pypi.python.org/pypi/tox/

0.8.0 - 2011-05-30
------------------

* Support for reading input from ``stdin`` for editing commands
* Supports listing bugs by label

0.7.0 - 2011-05-30
------------------

* Works with unpatched github2_ package now!
* No longer supports priorities, GitHub have dropped support for this feature

.. _github2: https://pypi.python.org/pypi/github2/

0.6.0 - 2011-04-09
------------------

* Display an issue's pull request in default templates
* Include pull request patch output with ``--patch`` option
* New template filter ``highlight`` for passing text through Pygments_

.. _Pygments: http://pygments.org/

0.5.0 - 2011-03-10
------------------

* Support for editing an existing bug's title and/or summary
* Support for re-opening closed bugs
* GitHub authorisation values can be read from the environment using
  ``GITHUB_USER`` and ``GITHUB_TOKEN``
* Labels are now included in list output
* argh_ is now required

.. _argh: https://pypi.python.org/pypi/argh/

0.4.0 - 2011-02-26
------------------

* Format Markdown output using terminal escapes

0.3.0 - 2011-02-26
------------------

* Renamed to ``gh_bugs``
* Support for different ordering methods in list and search output
* Add or remove multiple labels by repeating ``-add` or ``-remove`` option
* Templates are searched for in ``XDG_DATA_HOME/gh_bugs/``, any ``gh_bugs``
  directory in ``XDG_DATA_DIRS`` and finally the Python package directory
* Jinja_ is now required
* If termcolor_ is installed coloured output is produced
* Addition of a distutils_ ``setup.py``

.. _Jinja: http://jinja.pocoo.org/
.. _termcolor: https://pypi.python.org/pypi/termcolor/
.. _distutils: http://docs.python.org/install/index.html

0.2.0 - 2011-02-25
------------------

* Support for using an editor to write comments and open issues.

0.1.0 - 2010-11-02
------------------

* Initial release
