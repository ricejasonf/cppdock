#!/usr/bin/env python3
# Test that `cppdock update_source` clones and updates a mount source
# with a `repo`, following a `source.path` local override.
#
# Run offline against a local git repo.

import json
import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
cppdock_path = os.path.join(test_dir, '..', '..', 'cppdock')

def check(cond, message):
    if not cond:
        print('FAIL: ' + message)
        sys.exit(1)

def git(path, *args):
    return subprocess.check_output(['git', '-C', path] + list(args),
                                   text = True).strip()

# Make a repo with a commit on `branch` and return the commit.
def commit(repo, branch, name):
    git(repo, 'checkout', '-q', '-B', branch)
    with open(os.path.join(repo, 'file'), 'w') as fh:
        fh.write(name)
    git(repo, 'add', 'file')
    git(repo, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q',
        '-m', name)
    return git(repo, 'rev-parse', 'HEAD')

def run_cppdock(work_dir, args):
    process = subprocess.run([sys.executable, cppdock_path] + args,
                             cwd = work_dir, stdout = subprocess.PIPE,
                             stderr = subprocess.STDOUT, text = True)
    return process.returncode, process.stdout

def write_json(path, obj):
    with open(path, 'w') as fh:
        json.dump(obj, fh)

def test_update_source():
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, 'repo')
        work_dir = os.path.join(tmp, 'work')
        os.makedirs(work_dir)
        git(tmp, 'init', '-q', repo)
        first = commit(repo, 'feature', 'first')
        config = {'cppdock': {'name': 'test'},
                  'source': {'type': 'mount', 'repo': repo,
                             'tag': 'feature', 'path': './source'},
                  'platforms': {}}
        write_json(os.path.join(work_dir, 'cppdock.json'), config)
        source = os.path.join(work_dir, 'source')

        code, output = run_cppdock(work_dir, ['update_source'])
        check(code == 0, 'clone failed:\n' + output)
        check(git(source, 'rev-parse', 'HEAD') == first, 'clone not at tag')

        # Rewrite the branch, as a rebased fork does.
        git(repo, 'checkout', '-q', '--orphan', 'other')
        second = commit(repo, 'feature', 'second')
        code, output = run_cppdock(work_dir, ['update_source'])
        check(code == 0, 'update failed:\n' + output)
        check(git(source, 'rev-parse', 'HEAD') == second,
              'update did not follow a rewritten branch')

        with open(os.path.join(source, 'file'), 'w') as fh:
            fh.write('dirty')
        third = commit(repo, 'feature', 'third')
        code, output = run_cppdock(work_dir, ['update_source'])
        check(code != 0 and 'uncommitted changes' in output,
              'updated a checkout with uncommitted changes')
        check(git(source, 'rev-parse', 'HEAD') == second,
              'moved a checkout with uncommitted changes')

        other = os.path.join(tmp, 'elsewhere')
        write_json(os.path.join(work_dir, 'cppdock-local.json'),
                   {'source': {'path': other}})
        code, output = run_cppdock(work_dir, ['update_source'])
        check(code == 0, 'clone to the local path failed:\n' + output)
        check(git(other, 'rev-parse', 'HEAD') == third,
              'local source path not followed')
        with open(os.path.join(work_dir, 'cppdock.json')) as fh:
            check(json.load(fh)['source']['path'] == './source',
                  'local source path written to cppdock.json')

def test_no_repo():
    with tempfile.TemporaryDirectory() as work_dir:
        write_json(os.path.join(work_dir, 'cppdock.json'),
                   {'cppdock': {'name': 'test'}, 'platforms': {}})
        code, output = run_cppdock(work_dir, ['update_source'])
        check(code != 0 and '"repo"' in output,
              'update_source ran without a repo')

test_update_source()
test_no_repo()
print('PASS')
