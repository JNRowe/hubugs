Appendix
========

.. _bug_objects-label:

``Bug`` objects
---------------

.. attribute:: Bug.assignee(User)

   The user the issue is assigned to, if any.

.. attribute:: Bug.body(str)

   The full body of the issue.

.. attribute:: Bug.body_html(str)

   The full body of the issue rendered as HTML.

.. attribute:: Bug.closed_at(datetime.datetime)

   The date and time the issue was closed.

.. attribute:: Bug.closed_by(User)

   The user the issue was closed by, if closed.

.. attribute:: Bug.comments(int)

   The number of comments made on the issue.

.. attribute:: Bug.created_at(datetime.datetime)

   The date and time the issue was created.

.. attribute:: Bug.labels(list)

   ``Label`` objects associated with the issue.

.. attribute:: Bug.milestone(str)

   The milestone name associated with the issue, if any.

.. attribute:: Bug.number(int)

   The issue's number.

.. attribute:: Bug.pull_request(PullRequest)

   Pull request data associated with the issue.

.. attribute:: Bug.state(str)

   State of the issue, either ``open`` or ``closed``.

.. attribute:: Bug.title(str)

   The issue's title.

.. attribute:: Bug.updated_at(datetime.datetime)

   The date and time when the issue was last updated.

.. attribute:: Bug.user(User)

   The GitHub user that created the issue.

.. _comment_objects-label:

``Comment`` objects
-------------------

.. attribute:: Comment.body(str)

   The full text of the comment.

.. attribute:: Comment.body_html(str)

   The full text of the comment rendered as HTML.

.. attribute:: Comment.created_at(datetime.datetime)

   The date and time the comment was created.

.. attribute:: Comment.updated_at(datetime.datetime)

   The date and time when the comment was last updated.

.. attribute:: Comment.user(User)

   The GitHub user that created the comment.

.. _label_objects-label:

``Label`` objects
-----------------

.. attribute:: Label.color

   The colour value for the given label.

.. attribute:: Label.name

   The name given to the label.

.. _pullrequest_objects-label:

``PullRequest`` objects
-----------------------

.. attribute:: PullRequest.diff_url(str)

   URL for :program:`diff` output associated with the issue.

.. attribute:: PullRequest.patch_url(str)

   URL for the :program:`git format-patch` output associated with the issue.


.. _repo_objects-label:

``Repository`` objects
----------------------

.. attribute:: Repository.clone_url(str)

   Clone URL for fetching via HTTP.

.. attribute:: Repository.created_at(datetime.datetime)

   The date and time the repository was created.

.. attribute:: Repository.description(str)

   The description given to the repository

.. attribute:: Repository.fork(bool)

   Whether the repository is a fork of another on GitHub

.. attribute:: Repository.forks(int)

   The number of forks on GitHub

.. attribute:: Repository.git_url(str)

   Clone URL for fetching via ``git`` protocol.

.. attribute:: Repository.has_downloads(bool)

   Whether the repository has downloads enabled

.. attribute:: Repository.has_issues(bool)

   Whether the repository has issues enabled

.. attribute:: Repository.has_wiki(bool)

   Whether the repository has the wiki enabled

.. attribute:: Repository.homepage(str)

   The homepage of the repository

.. attribute:: Repository.html_url(str)

   The main project page on GitHub

.. attribute:: Repository.language(str)

   The programming language used

.. attribute:: Repository.master_branch(str)

   The repository's defined master branch

.. attribute:: Repository.mirror_url(str)

   The original location of a repository, if a mirror

.. attribute:: Repository.name(str)

   The repository's name

.. attribute:: Repository.open_issues(int)

   The number of open issues in a repository

.. attribute:: Repository.owner(User)

   The owner of the repository

.. attribute:: Repository.private(bool)

   Whether the repository is set as private

.. attribute:: Repository.pushed_at(datetime.datetime)

   The last time the repository's content was updated

.. attribute:: Repository.size(int)

   The size of the repository

.. attribute:: Repository.watchers(int)

   The number of watchers of the repository

.. _user_objects-label:

``User`` objects
----------------

.. attribute:: avatar_url(str)

   The location of the user's avatar

.. attribute:: gravatar_id(str)

   The hash identifier for fetching images from `gravatar <gravatar.com>`__

.. attribute:: login(str)

   The user's login name on GitHub
