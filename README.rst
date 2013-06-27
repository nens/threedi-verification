threedi-verification
==========================================

Introduction

Usage, etc.


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
