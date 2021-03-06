Changelog of threedi-verification
===================================================


0.3 (unreleased)
----------------

- Add checking for ini files (for FLOW) due to changes in python-flow.

- Fix bug with plots being overwritten. Now they are uniquely identified and
  saved per test run using the test_run_id.

- Also include timestamp of index.txt when checking FLOW test case version.

- Add categories for test cases. Adjust vertical line in plots.

- Add csv files to the timestamp check for new testruns (only for FLOW).

- Big changes: add functionality for running different libraries, i.e.,
  at the moment, both subgrid and the new flow library.

- Point update_testbank.sh script to production model databank (hg.lizard.net).

- Add update_testbank_valgrind.sh to not let it checkout testbank_flow. This is not necessary.


0.2 (2014-06-25)
----------------

- We're slightly less strict in time checking. We only warn in the logfile,
  too, btw if we encounter an error:

  "Didn't find proper time 18000.0, but after rounding we did find 18000.0517827"

- Looking at 'margin' parameter in csv. Can be both absolute and relative
  (indicated by a % sign).

- Fix for NaN results.

- Re-worked the interface to be a django app.


0.1 (2013-07-01)
----------------

- Initial project structure created with nensskel 1.34.dev0.

- Copied verification part from the python-subgrid library.

- Got everything mostly working. Netcdf reading, mdu finding, csv
  reading and checking the values.
