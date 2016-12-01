# Overview

Useful tools for summarizing unexpected WPT failures, then diving deep into
partiular failing test output.

NOTE: this is designed to work with logs of running WPT under rr at the moment,
and in particular a patched version of rr that always prints out the directory
where the recording is stored.

## Display all test files with unexpected results

python main.py wpt.log

## Display process output of a particular test, grouped by timestamps

python main.py wpt.log some-failing-test.html

## Display structured log contents for a particular test

python main.py wpt.log some-failing-test.html -v
