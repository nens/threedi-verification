threedi-verification
==========================================

This program tests a directory structure of mdu/csv files that all
together check the subgrid fortran library. What it does:

- Traverse a directory structure (directory passed on the commandline
  as the single argument).

- Find ``*.mdu`` files and call them with the subgrid executable.

- Find ``*.csv`` files belonging to the ``.mdu``.

- Read instructions from the ``.csv`` which tell us the x/y
  coordinate, parameter and expected value (mostly, there are
  exceptions, like summing all values).

- Record the results and generate html pages with the results.


Test cases
----------

N&S is preparing model test cases ("model unit tests"), testing
individual bits and pieces of functionality. It works on linux only at
the moment, but that's just because it expects an
``/opt/3di/bin/subgridf90`` binary (so that's fixable).

It also requires a mercurial (``hg``) to be installed.

A django site shows the tests results, so the regular django setup is needed::

    $ bin/django syncdb
    $ bin/django migrate
    $ bin/django runserver  # To run the site.

Run ``./update_testbank.sh`` to get the current set of test cases in
the ``testbank/`` subdirectory. (You might need to enable the
largefile mercurial extension in your ``~/.hgrc``). After that::

    $ bin/django import_test_cases
    $ bin/django run_simulations

Or in case you want to test with a specific testcase (especially when
developing), use the ``run_simulation`` (without an ``s``) command and pass in
an mdu file::

    $ bin/django run_simulation testbank/4_09/4_09_07/4_09_07.mdu

This generates some html files into the ``var/html/`` directory.
The html output is also generated on jenkins:
http://jenkins.3di.lizard.net/testresults/ .


3Di subgrid library location
----------------------------

Currently ``/opt/3di/bin/subgridf90`` is executed directly, so normally that'd
be the most recently compiled and installed version. At least, on the jenkins
machine that's the case: if the compilation of the "subgridf90" task succeeds,
a "make install" is automatically done.

When running locally and using the debian packages, you'll need to symlink
``/opt/3di/`` to the latest ``/opt/3di/*`` version. Or compile it by hand.
