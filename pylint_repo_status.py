#!/usr/bin/python
"""
Finds the git commit hash of:
    - the branch head that has been most recently pushed
    - that hasn't already had a pylint run started on it
and:
    - sends a repo status of 'pending' with context 'pylint'
    - runs pylint
    - send a repo status of 'success' or 'failure'
"""

import logging
from subprocess import check_output

logging.basicConfig(level=logging.DEBUG)

def git_fetch():
    """Make sure our local has good remote understanding"""
    output = check_output(['git', 'fetch'])


def unmerged_branch_heads(limit=100):
    """Get just the githash of the the unmerged branch heads"""
    output = check_output(['git', 'branch',
        '--remotes',
        '--verbose',
        '--no-merged', 'master',
        '--list',
        '--no-abbrev'
        ])
    return [line.split()[1] for line in output.rstrip().split("\n")[:limit]]

def claim_commit(sha):
    """returns True if we should act on this sha, and False if already done"""
    # Uses double-check almost certainly wrongly assuming github is consistent


def pylint_latest():
    git_fetch()
    logging.debug(unmerged_branch_heads())


if __name__ == "__main__":
    pylint_latest()
