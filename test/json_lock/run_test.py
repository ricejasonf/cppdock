#!/usr/bin/env python3
# Test that `cppdock init` locks every dep in cppdock.json.
#
# Run offline: fake `git` and `podman` commands on PATH stand in for
# `git ls-remote` and the image registry.

import hashlib
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

fake_git = f"""#!/bin/sh
# Answer `git ls-remote https://github.com/ricejasonf/nbdl`.
[ "$1" = ls-remote ] && [ "$2" = https://github.com/ricejasonf/nbdl ] || exit 1
echo "{nbdl_master_revision}\trefs/heads/master"
echo "{nbdl_develop_revision}\trefs/heads/develop"
"""

fake_podman = """#!/bin/sh
# Answer `pull` and `image inspect` with a digest of the image reference.
[ "$1" = pull ] && exit 0
[ "$1 $2" = "image inspect" ] || exit 1
digest=$(printf %s "$3" | sha256sum | cut -d' ' -f1)
echo "[{\\"RepoDigests\\": [\\"$3@sha256:$digest\\"]}]"
"""

# Get the digest the fake podman reports for an image reference.
def image_digest(image_ref):
    return 'sha256:' + hashlib.sha256(image_ref.encode()).hexdigest()

def write_script(path, text):
    with open(path, 'w') as fh:
        fh.write(text)
    os.chmod(path, 0o755)

def check(cond, message):
    if not cond:
        print('FAILURE: ' + message)
        sys.exit(1)

# Run `cppdock init` on a copy of `config_obj`; return its exit code and result.
def run_init(config_obj):
    with tempfile.TemporaryDirectory() as work_dir:
        bin_dir = os.path.join(work_dir, 'bin')
        os.mkdir(bin_dir)
        write_script(os.path.join(bin_dir, 'git'), fake_git)
        write_script(os.path.join(bin_dir, 'podman'), fake_podman)
        config_path = os.path.join(work_dir, 'cppdock.json')
        with open(config_path, 'w') as fh:
            json.dump(config_obj, fh)

        env = dict(os.environ)
        env['PATH'] = bin_dir + os.pathsep + env['PATH']
        env.pop('CPPDOCK_ENGINE', None)
        result = subprocess.run([sys.executable, cppdock_path, 'init'],
                                cwd=work_dir, env=env,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        with open(config_path) as fh:
            return result.returncode, json.load(fh)

def load_fixture(name):
    with open(os.path.join(test_dir, name)) as fh:
        return json.load(fh)

def test_lock():
    returncode, config = run_init(load_fixture('cppdock.json'))
    check(returncode == 0, '`cppdock init` failed')
    platforms = config['platforms']
    linux_deps = platforms['my_linux_x64']['deps']
    emscripten_deps = platforms['my_emscripten']['deps']
    check(linux_deps[0][0]['revision'] == nbdl_master_revision,
          'nbdl master not locked to the remote branch')
    check(emscripten_deps[0][0]['revision'] == nbdl_develop_revision,
          'nbdl develop not locked to the remote branch')
    check(linux_deps[1][0]['revision'] == hana_revision
          and emscripten_deps[1][0]['revision'] == hana_revision,
          'hard coded hana revision changed')
    check(linux_deps[2][0]['revision']
          == image_digest('docker.io/ricejasonf/cppdock:latest'),
          'docker dep not locked to the docker.io image')

def test_registry():
    returncode, config = run_init(load_fixture('cppdock-registry.json'))
    check(returncode == 0, '`cppdock init` failed with registries')
    deps = config['platforms']['main']['deps']
    check(deps[0][0]['revision']
          == image_digest('registry.example.com/ricejasonf/a:latest'),
          'docker dep not locked to the default_registry image')
    check(deps[1][0]['revision']
          == image_digest('localhost/ricejasonf/b:latest'),
          'docker dep not locked to its own registry image')

def test_registry_in_name():
    config = load_fixture('cppdock-registry.json')
    config['platforms']['main']['deps'][0][0]['name'] = 'ghcr.io/ricejasonf/a'
    returncode, _ = run_init(config)
    check(returncode != 0, 'docker dep name with a registry was accepted')

test_lock()
test_registry()
test_registry_in_name()
print('PASS')
