pylint-to-github
================

I spent a few hours trying to get the Jenkins Github plugin to:
 - run pylint on all remote branch heads that:
    - arent' too old
    - haven't already had pylint run on them
 - send the repo status back to github
 
I'm sure it's possible, but the repo statuses weren't posting, the wrong branches were getting built,
and it was easier to write a quick script.


Requirements
------------
The usual python stuff, and, of course, the git binary and pylint available in `$PATH`
 
Configuration
-------------
 - update the repo owner on line 21
 - update the repo name on line 22
 - if the repo doesn't have a top level `pylint.rc` add one
 - set an environment variable called `GITHUB_TOKEN` with oauth-juice enough to read and write repo

Running
-------
The script should be run from within a checkout of the repository it will be testing.
It's suitable for running regularly from cron or triggered by a github push hook to Jenkins.
Each instance of the script needs it own local checkout, but running multiple copies does provide pylint
parallelization without duplication of scans.
