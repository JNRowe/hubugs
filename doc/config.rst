Configuration
=============

Before :program:`hubugs` can operate on issues you must generate an OAuth_
token.  :program:`hubugs` provides functionality to do this:

.. code-block:: sh

    ▶ hubugs setup
    GitHub user? [JNRowe]
    GitHub password? <password>
    Support private repositories? (Y/n) y
    Configuration complete!

.. note::

   You can revoke the generated token at any time from the `GitHub settings`_
   page.

If you wish to set the authorisation token from the command line you can use the
:envvar:`HUBUGS_TOKEN` environment variable.  For example:

.. code-block:: sh

    ▶ HUBUGS_TOKEN=xxx hubugs open

.. _OAuth: http://oauth.net/
.. _GitHub settings: https://github.com/settings/applications/
