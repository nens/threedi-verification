Changelog of threedi-verification
===================================================


0.2 (unreleased)
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
