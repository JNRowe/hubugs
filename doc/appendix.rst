Appendix
========

.. _bug_objects-label:

``Bug`` objects
---------------

.. attribute:: Bug.body(str)

   The full body of the issue.

.. attribute:: Bug.closed_at(datetime.datetime)

   The date and time the issue was closed.

.. attribute:: Bug.created_at(datetime.datetime)

   The date and time the issue was created.

.. attribute:: Bug.diff_url(str)

   URL for :program:`diff` output associated with the issue.

.. attribute:: Bug.labels(list)

   Labels associated with the issue.

.. attribute:: Bug.number(int)

   The issue's number.

.. attribute:: Bug.patch_url(str)

   URL for the :program:`git format-patch` output associated with the issue

.. attribute:: Bug.position(int)

   The position of the issue in the bug list. (deprecated in GitHub API)

.. attribute:: Bug.pull_request_url(str)

   URL for the issue's related pull request.

.. attribute:: Bug.state(str)

   State of the issue, either ``open`` or ``closed``.

.. attribute:: Bug.title(str)

   The issue's title.

.. attribute:: Bug.updated_at(datetime.datetime)

   The date and time when the issue was last updated.

.. attribute:: Bug.user(str)

   The GitHub username of the user that created the issue.

.. attribute:: Bug.votes(int)

   Number of votes the issue has received.

.. _comment_objects-label:

``Comment`` objects
-------------------

.. attribute:: Comment.body(str)

   The full text of the comment.

.. attribute:: Comment.created_at(datetime.datetime)

   The date and time the comment was created.

.. attribute:: Comment.id(int)

   The comment's id.

.. attribute:: Comment.updated_at(datetime.datetime)

   The date and time when the comment was last updated.

.. attribute:: Comment.user(str)

   The GitHub username of the user that created the comment.
