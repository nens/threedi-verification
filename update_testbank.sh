#!/bin/sh
# Script that updates (and creates, if necessary) a bunch of
# testcases.
if [ ! -d testbank ]
then
    echo "testbank subdir doesn't exist, cloning it"
    hg clone http://hg.lizard.net/testbank
fi
cd testbank;
hg pull -u
cd ..

# Do the same for the flow test cases.
if [ ! -d testbank_flow ]
then
    echo "testbank_flow subdir doesn't exist, cloning it"
    hg clone http://hg.lizard.net/testbank_flow
fi
cd testbank_flow;
hg purge --all  # purge untracked + ignored files
hg pull -u
