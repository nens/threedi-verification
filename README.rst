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

Run ``./update_testbank.sh`` to get the current set of test cases in
the ``testbank/`` subdirectory. (You might need to enable the
largefile mercurial extension in your ``~/.hgrc``). After that::

    $ bin/verify testbank

This generates some html files into the current directory. The html
output is also generated on jenkins:
http://jenkins.3di.lizard.net/testresults/ .
