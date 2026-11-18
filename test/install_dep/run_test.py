#!/usr/bin/env python3
# Test that `cppdock install_dep` installs several git deps in one stage.
#
# Run each `install_dep` in a container with no network: a driver replaces
# `urlopen` with a lookup of local archives laid out like GitHub's.
# Set CPPDOCK_TEST_IMAGE to the image to run in (it needs python3.)

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

test_dir = os.path.dirname(os.path.abspath(__file__))
cppdock_path = os.path.realpath(os.path.join(test_dir, '..', '..', 'cppdock'))
engine = os.environ.get('CPPDOCK_ENGINE', 'podman')
test_image = os.environ.get('CPPDOCK_TEST_IMAGE',
                            'docker.io/ricejasonf/cppdock:latest')

# Fail unless the source has only this dep's files and the build directory
# is empty, then install the source and leave a file in the build directory.
recipe = """#!/bin/sh
set -e
[ "$(ls -A /opt/src | wc -l)" = 1 ] || { echo "stale /opt/src"; exit 1; }
[ -z "$(ls -A /opt/build)" ] || { echo "stale /opt/build"; exit 1; }
cp -r /opt/src/. /opt/install/
touch /opt/build/CMakeCache.txt
"""

# Run `cppdock install_dep` for each dep with the archive of its revision.
driver = """
import io, os, runpy, shutil, sys, urllib.request
def urlopen(url):
    name = url.removeprefix('https://github.com/').replace('/', '-')
    return open(os.path.join('/test/archives', name), 'rb')
urllib.request.urlopen = urlopen
for dir in ['/opt/install', '/opt/build', '/usr/local/src']:
    os.makedirs(dir, exist_ok=True)
os.chdir('/usr/local/src')
for revision, repo in [x.split() for x in sys.argv[1:]]:
    shutil.copy('/test/recipe', '/opt/recipe_script')
    sys.argv = ['cppdock', 'install_dep', 'linux_x64', revision, repo]
    try:
        runpy.run_path('/usr/local/bin/cppdock', run_name='__main__')
    except SystemExit as e:
        if e.code:
            sys.exit(e.code)
print(' '.join(sorted(os.listdir('/opt/install'))))
"""

deps = [('1' * 40, 'ricejasonf/a'), ('2' * 40, 'ricejasonf/b')]

def check(cond, message):
    if not cond:
        print('FAILURE: ' + message)
        sys.exit(1)

def have_test_image():
    if shutil.which(engine) is None:
        return False
    return subprocess.run([engine, 'image', 'exists', test_image]).returncode == 0

# Write a GitHub style archive of `repo` with one file named after it.
def write_archive(archive_dir, revision, repo):
    name = repo.split('/')[1]
    path = os.path.join(archive_dir, f'{repo.replace("/", "-")}-archive-'
                                     f'{revision}.zip')
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr(f'{name}-{revision}/{name}.txt', name)

def run_install_deps(deps):
    with tempfile.TemporaryDirectory() as work_dir:
        archive_dir = os.path.join(work_dir, 'archives')
        os.mkdir(archive_dir)
        for revision, repo in deps:
            write_archive(archive_dir, revision, repo)
        for name, text in [('recipe', recipe), ('driver.py', driver)]:
            with open(os.path.join(work_dir, name), 'w') as fh:
                fh.write(text)
        os.chmod(os.path.join(work_dir, 'recipe'), 0o755)
        return subprocess.run(
            [engine, 'run', '--rm', '--network=none',
             '--volume', f'{work_dir}:/test:ro,z',
             '--volume', f'{cppdock_path}:/usr/local/bin/cppdock:ro,z',
             test_image, 'python3', '/test/driver.py'] +
            [f'{revision} {repo}' for revision, repo in deps],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def test_two_deps_in_one_stage():
    result = run_install_deps(deps)
    check(result.returncode == 0,
          'second dep in a stage failed to install:\n' + result.stdout)
    check(result.stdout.splitlines()[-1] == 'a.txt b.txt',
          'deps not both installed:\n' + result.stdout)

if not have_test_image():
    print(f'SKIP: no {engine} image {test_image}')
    sys.exit(0)
test_two_deps_in_one_stage()
print('PASS')
