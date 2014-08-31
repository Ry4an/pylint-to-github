#!/usr/bin/python
"""
Finds the git commit hash of branches that don't yet have a pylint status and:
    - sends a repo status of 'pending' with context 'pylint'
    - checks out that revision
    - runs pylint
    - send a repo status of 'success' or 'failure'
"""

import logging
import json
import requests
import os
from subprocess import check_output, check_call
from time import sleep
from pylint import epylint as lint  # we like version 1.1.0

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('pylint_repo_status')

OWNER = "DramaFever"
REPO = "hacks" # FIXME "www"
TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_BASE = "https://api.github.com/repos/{owner}/{repo}".format(owner=OWNER, repo=REPO)
STATUSES_FOR_REF = GITHUB_BASE + "/commits/{ref}/statuses?access_token={token}"
CREATE_STATUS_FOR_REF = GITHUB_BASE + "/statuses/{ref}?access_token={token}"

def git_fetch():
    """Make sure our local has good remote understanding"""
    output = check_output(['git', 'fetch'])


def unmerged_branch_heads():
    """Get just the githash of the the unmerged branch heads -- sadly alphabetized"""
    output = check_output(['git', 'branch',
        '--remotes',
        '--verbose',
        '--no-merged', 'master',
        '--list',
        '--no-abbrev'
        ])
    return [line.split()[1] for line in output.rstrip().split("\n")]

def get_most_recent_status_for(sha):
    """get current pylint status for given sha, or None if no statuses found"""
    resp = requests.get(STATUSES_FOR_REF.format(ref=sha, token=TOKEN))
    statuses = [status for status in json.loads(resp.content) if status['context'] == 'pylint']
    return statuses[0] if statuses else None

def create_status_for(sha, state, description=None, context="pylint", target_url=None):
    """create a new status for the given sha w/ specified parameters, returns id"""
    post = {'state': state, 'context': context}
    if target_url:
        post['target_url'] = target_url
    if description:
        post['description'] = description
    logger.debug(post)
    resp = requests.post(CREATE_STATUS_FOR_REF.format(ref=sha, token=TOKEN),
            data=json.dumps(post))
    logger.debug("OUTPUT={}".format(resp.content))
    return json.loads(resp.content)['id']

def try_claim_commit(sha):
    """returns True if we should act on this sha, and False if already done"""
    # fake double-check has a non-fatal race condition, but better than nothing
    last_status = get_most_recent_status_for(sha)
    if last_status and last_status['state'] != 'failure':
        return False
    my_id = create_status_for(sha, 'pending')
    sleep(1)
    cur_status = get_most_recent_status_for(sha)
    return my_id == cur_status['id']  # did my claim stick?

def checkout(sha):
    """check out specified sha"""
    check_call(['git', 'checkout', sha])

def pylint_check(sha):
    """checks out and runs pylint on the given sha, returning True if good"""
    # lint.py_run(...)
    return 1 / 0

def pylint_branches():
    # FIXME git_fetch()
    for sha in unmerged_branch_heads():
        if not try_claim_commit(sha):
            continue  # already done on in progress
        logger.debug("claimed {}".format(sha))
        try:
            checkout(sha)
            create_status_for(sha, 'success' if pylint_check(sha) else 'error')
        except:
            logger.exception("Problem pylinting {}".format(sha))
            create_status_for(sha, 'failure')
        break  # FIXME remove

if __name__ == "__main__":
    pylint_branches()
