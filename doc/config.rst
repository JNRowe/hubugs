Configuration
=============

Before using :program:`hubugs` you must declare your authentication settings to
enable access to the GitHub API.

You first need to define your GitHub user name:

.. code-block:: sh

    ▶ git config --global github.user '<username>'

And then you need to define your GitHub API token, this can be found in the
`account admin`_ tab of your GitHub `account page`_:

.. code-block:: sh

    ▶ git config --global github.token '<token>'

.. note::

   If you change your GitHub password your ``github.token`` setting will be
   invalid, and you must set it again.

If you wish to set the authentication information from the command line you can
use the :envvar:`GITHUB_USER` and :envvar:`GITHUB_TOKEN` environment variables.
For example:

.. code-block:: sh

    ▶ GITHUB_USER=jnrowe GITHUB_TOKEN=xxx hubugs open

.. _account admin: https://github.com/account/admin
.. _account page: https://github.com/account
