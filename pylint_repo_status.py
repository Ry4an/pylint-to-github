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
import datetime
import os
from subprocess import check_output, check_call, CalledProcessError
from time import sleep

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('pylint_repo_status')

OWNER = "DramaFever"
REPO = "www"
TOKEN = os.environ['GITHUB_TOKEN']
GITHUB_BASE = "https://api.github.com/repos/{owner}/{repo}".format(owner=OWNER, repo=REPO)
STATUSES_FOR_REF = GITHUB_BASE + "/commits/{ref}/statuses?access_token={token}"
CREATE_STATUS_FOR_REF = GITHUB_BASE + "/statuses/{ref}?access_token={token}"
PYLINT_RC = "./pylint.rc"

def git_fetch():
    """Make sure our local has good remote understanding"""
    check_call(['git', 'fetch'])

def unmerged_branch_heads():
    """Get just the githash of the the unmerged branch heads -- sadly alphabetized"""
    output = check_output(['git', 'branch',
        '--remotes',
        '--verbose',
        '--no-merged', 'master',
        '--list',
        '--no-abbrev'
        ])
    return [line.split()[1] for line in output.rstrip().split("\n") if not '->' in line]

def only_recent(iterator, delta=datetime.timedelta(days=1)):
    """filter that passes only commits newer than timedelta, default 1 day"""
    for sha in iterator:
        logger.debug("date checking '{}'".format(sha))
        datetime_str = check_output(['git', 'show', '-s', '--format=%ct', sha])
        commit_time = datetime.datetime.utcfromtimestamp(int(datetime_str))
        if datetime.datetime.utcnow() - commit_time < delta:
            yield sha

def get_most_recent_status_for(sha):
    """get current pylint status for given sha, or None if no statuses found"""
    resp = requests.get(STATUSES_FOR_REF.format(ref=sha, token=TOKEN))
    statuses = [status for status in json.loads(resp.content) if status['context'] == 'pylint']
    return statuses[0] if statuses else None

def create_status_for(sha, state, description=None, context="pylint", target_url=None):
    """create a new status for the given sha w/ specified parameters, returns id"""
    logger.debug("creating status for sha='{}'".format(sha))
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
    if last_status and last_status['state'] != 'error':
        return False  # already done or in progress
    my_id = create_status_for(sha, 'pending', 'running pylint')
    sleep(1)
    cur_status = get_most_recent_status_for(sha)
    return my_id == cur_status['id']  # did my claim stick?

def checkout(sha):
    """check out specified sha"""
    check_call(['git', 'checkout', sha])

def pylint_check(sha):
    """checks out and runs pylint on the given sha, returning True if good"""
    checkout(sha)
    args = ['pylint', '--rcfile', PYLINT_RC, 'dramafever']
    logger.debug("args={}".format(args))
    try:
        output = check_output(args)
    except CalledProcessError as ex:
        logger.info("PYLINT EXIT={} OUTPUT='{}'".format(ex.returncode, ex.output))
        return False
    if output:
        logger.info("PYLINT OUTPUT='{}'".format(output))
        return False
    return True

def pylint_branches():
    """run pylint across all new enough branches and report back status"""
    git_fetch()
    for sha in only_recent(unmerged_branch_heads()):
        if not try_claim_commit(sha):
            continue  # already done on in progress
        logger.debug("claimed {}".format(sha))
        try:
            if pylint_check(sha):
                create_status_for(sha, 'success', 'pylint passed')
            else :
                create_status_for(sha, 'failure', 'pylint failed')
        except:
            logger.exception("Problem pylinting {}".format(sha))
            create_status_for(sha, 'error', 'exception during pylint')

if __name__ == "__main__":
    pylint_branches()
