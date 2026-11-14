#!/usr/bin/env python3
# Test that `cppdock init` locks every dep in cppdock.json.
#
# Run offline: fake `git` and `podman` commands on PATH stand in for
# `git ls-remote` and the image registry.

import json
import os
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
cppdock_path = os.path.join(test_dir, '..', '..', 'cppdock')

hana_revision = 'd9da8776aa1142c0f92a38d49829ae5c3e86c7bc'
nbdl_master_revision = '1' * 40
nbdl_develop_revision = '2' * 40
cppdock_digest = 'sha256:' + '3' * 64

fake_git = f"""#!/bin/sh
# Answer `git ls-remote https://github.com/ricejasonf/nbdl`.
[ "$1" = ls-remote ] && [ "$2" = https://github.com/ricejasonf/nbdl ] || exit 1
echo "{nbdl_master_revision}\trefs/heads/master"
echo "{nbdl_develop_revision}\trefs/heads/develop"
"""

fake_podman = f"""#!/bin/sh
# Answer `pull` and `image inspect` for docker.io/ricejasonf/cppdock:latest.
[ "$2" = docker.io/ricejasonf/cppdock:latest ] && [ "$1" = pull ] && exit 0
[ "$3" = docker.io/ricejasonf/cppdock:latest ] && [ "$1 $2" = "image inspect" ] || exit 1
echo '[{{"RepoDigests": ["docker.io/ricejasonf/cppdock@{cppdock_digest}"]}}]'
"""

def write_script(path, text):
    with open(path, 'w') as fh:
        fh.write(text)
    os.chmod(path, 0o755)

def check(cond, message):
    if not cond:
        print('FAILURE: ' + message)
        sys.exit(1)

def start():
    with tempfile.TemporaryDirectory() as work_dir:
        bin_dir = os.path.join(work_dir, 'bin')
        os.mkdir(bin_dir)
        write_script(os.path.join(bin_dir, 'git'), fake_git)
        write_script(os.path.join(bin_dir, 'podman'), fake_podman)
        shutil.copy(os.path.join(test_dir, 'cppdock.json'), work_dir)

        env = dict(os.environ)
        env['PATH'] = bin_dir + os.pathsep + env['PATH']
        env.pop('CPPDOCK_ENGINE', None)
        result = subprocess.run([sys.executable, cppdock_path, 'init'],
                                cwd=work_dir, env=env)
        check(result.returncode == 0, '`cppdock init` failed')

        with open(os.path.join(work_dir, 'cppdock.json')) as fh:
            platforms = json.load(fh)['platforms']

    linux_deps = platforms['my_linux_x64']['deps']
    emscripten_deps = platforms['my_emscripten']['deps']
    check(linux_deps[0][0]['revision'] == nbdl_master_revision,
          'nbdl master not locked to the remote branch')
    check(emscripten_deps[0][0]['revision'] == nbdl_develop_revision,
          'nbdl develop not locked to the remote branch')
    check(linux_deps[1][0]['revision'] == hana_revision
          and emscripten_deps[1][0]['revision'] == hana_revision,
          'hard coded hana revision changed')
    check(linux_deps[2][0]['revision'] == cppdock_digest,
          'docker dep not locked to the image digest')
    print('PASS')

start()
