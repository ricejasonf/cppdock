#!/usr/bin/env python3
# Test that `cppdock init` locks every dep in cppdock.json and that
# `cppdock build` fetches and verifies locked docker deps.
#
# Run offline: fake `git` and `podman` commands on PATH stand in for
# `git ls-remote`, the local image store and the image registry.

import hashlib
import json
import os
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

# Model the image store and the registry as directories of image inspect
# objects named by image reference, and log every command.
fake_podman = """#!/usr/bin/env python3
import json, os, shutil, sys
state = os.environ['FAKE_ENGINE_STATE']
local, remote = os.path.join(state, 'local'), os.path.join(state, 'remote')
def path(store, ref):
    return os.path.join(store, ref.replace('/', '%'))
args = sys.argv[1:]
with open(os.path.join(state, 'log'), 'a') as fh:
    fh.write(' '.join(args) + '\\n')
match args:
    case ['image', 'inspect', ref]:
        if not os.path.exists(path(local, ref)):
            sys.exit(1)
        with open(path(local, ref)) as fh:
            print(json.dumps([json.load(fh)]))
    case ['pull', ref]:
        if not os.path.exists(path(remote, ref)):
            sys.exit(1)
        shutil.copy(path(remote, ref), path(local, ref))
    case ['tag', src, dst]:
        shutil.copy(path(local, src), path(local, dst))
    case ['push', ref]:
        shutil.copy(path(local, ref), path(remote, ref))
    case ['buildx', 'build', *options, context]:
        with open(os.path.join(state, 'dockerfiles'), 'a') as fh:
            fh.write(sys.stdin.read())
        tag = [x for x in options if x.startswith('--tag=')][0][6:]
        with open(path(local, tag), 'w') as fh:
            json.dump({'RootFS': {'Layers': ['sha256:' + tag]}}, fh)
    case _:
        sys.exit(1)
"""

def layers_of(name):
    return ['sha256:' + hashlib.sha256(name.encode()).hexdigest()]

# Get the layers lock cppdock should compute for `layers`.
def layers_lock(layers):
    data = ''.join(layer + '\n' for layer in layers)
    return 'layers:sha256:' + hashlib.sha256(data.encode()).hexdigest()

def lock_tag(image_name, layers):
    return image_name + ':layers-sha256-' + layers_lock(layers).split(':')[2]

# Make an inspect object with the digest of its manifest, if any.
def image(image_name, layers, digest = None):
    return {'RootFS': {'Layers': layers}, 'Digest': digest,
            'RepoDigests': [f'{image_name}@{digest}'] if digest else []}

def write_script(path, text):
    with open(path, 'w') as fh:
        fh.write(text)
    os.chmod(path, 0o755)

def check(cond, message):
    if not cond:
        print('FAILURE: ' + message)
        sys.exit(1)

class Result:
    pass

# Run cppdock `args` on a copy of `config_obj` with images in the fake
# `local` and `remote` stores ({ref: inspect object}).
def run_cppdock(args, config_obj, local = {}, remote = {}, files = {}):
    with tempfile.TemporaryDirectory() as work_dir:
        for name, text in files.items():
            with open(os.path.join(work_dir, name), 'w') as fh:
                fh.write(text)
        bin_dir = os.path.join(work_dir, 'bin')
        state_dir = os.path.join(work_dir, 'state')
        os.mkdir(bin_dir)
        for store, images in [('local', local), ('remote', remote)]:
            os.makedirs(os.path.join(state_dir, store))
            for ref, inspect in images.items():
                with open(os.path.join(state_dir, store,
                                       ref.replace('/', '%')), 'w') as fh:
                    json.dump(inspect, fh)
        write_script(os.path.join(bin_dir, 'git'), fake_git)
        write_script(os.path.join(bin_dir, 'podman'), fake_podman)
        config_path = os.path.join(work_dir, 'cppdock.json')
        with open(config_path, 'w') as fh:
            json.dump(config_obj, fh)

        env = dict(os.environ)
        env['PATH'] = bin_dir + os.pathsep + env['PATH']
        env['FAKE_ENGINE_STATE'] = state_dir
        env.pop('CPPDOCK_ENGINE', None)
        process = subprocess.run([sys.executable, cppdock_path] + args,
                                 cwd=work_dir, env=env,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True)
        result = Result()
        result.returncode = process.returncode
        result.output = process.stdout
        with open(config_path) as fh:
            result.config = json.load(fh)
        def stored(store):
            return set(ref.replace('%', '/') for ref in
                       os.listdir(os.path.join(state_dir, store)))
        result.local = stored('local')
        result.remote = stored('remote')
        def read(name):
            path = os.path.join(state_dir, name)
            return open(path).read() if os.path.exists(path) else ''
        result.log = read('log').splitlines()
        result.dockerfiles = read('dockerfiles')
        return result

def pulled(result):
    return [line.split()[1] for line in result.log if line.startswith('pull')]

def load_fixture(name):
    with open(os.path.join(test_dir, name)) as fh:
        return json.load(fh)

cppdock_image = 'docker.io/ricejasonf/cppdock'
cppdock_layers = layers_of(cppdock_image)
cppdock_digest = 'sha256:' + '3' * 64
cppdock_lock_ref = lock_tag(cppdock_image, cppdock_layers)

def test_lock_digest():
    result = run_cppdock(['init'], load_fixture('cppdock.json'), remote = {
        cppdock_image + ':latest':
            image(cppdock_image, cppdock_layers, cppdock_digest)})
    check(result.returncode == 0, '`cppdock init` failed')
    platforms = result.config['platforms']
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
          'image without a lock tag not locked to its manifest digest')

def test_lock_layers():
    result = run_cppdock(['init'], load_fixture('cppdock.json'), remote = {
        cppdock_image + ':latest':
            image(cppdock_image, cppdock_layers, cppdock_digest),
        cppdock_lock_ref:
            image(cppdock_image, cppdock_layers, cppdock_digest)})
    check(result.returncode == 0, '`cppdock init` failed with a lock tag')
    deps = result.config['platforms']['my_linux_x64']['deps']
    check(deps[2][0]['revision'] == layers_lock(cppdock_layers),
          'image with a lock tag not locked to its layers')

def test_lock_local():
    local_layers = layers_of('local build')
    local_image = image(cppdock_image, local_layers)
    result = run_cppdock(['init'], load_fixture('cppdock.json'), local = {
        cppdock_image + ':latest': local_image,
        lock_tag(cppdock_image, local_layers): local_image},
        remote = {cppdock_image + ':latest':
            image(cppdock_image, cppdock_layers, cppdock_digest)})
    check(result.returncode == 0, '`cppdock init` failed with a local image')
    check(pulled(result) == [], '`cppdock init` pulled an image that is local')
    deps = result.config['platforms']['my_linux_x64']['deps']
    check(deps[2][0]['revision'] == layers_lock(local_layers),
          'docker dep not locked to the local image')

def test_lock_unreleased():
    result = run_cppdock(['init'], load_fixture('cppdock.json'), local = {
        cppdock_image + ':latest': image(cppdock_image, cppdock_layers)})
    check(result.returncode != 0,
          'local image with no lock tag and no digest was locked')

def test_lock_stale_digest():
    stale_digest = 'sha256:' + '4' * 64
    result = run_cppdock(['init'], load_fixture('cppdock.json'), local = {
        cppdock_image + ':latest':
            image(cppdock_image, cppdock_layers, stale_digest)},
        remote = {cppdock_image + ':latest':
            image(cppdock_image, cppdock_layers, cppdock_digest)})
    check(result.returncode == 0, '`cppdock init` failed with a local digest')
    deps = result.config['platforms']['my_linux_x64']['deps']
    check(deps[2][0]['revision'] == cppdock_digest,
          'docker dep locked to a digest the registry does not have')

def test_registry():
    a_image = 'registry.example.com/ricejasonf/a'
    b_image = 'localhost/ricejasonf/b'
    base_image = 'registry.example.com/ricejasonf/cppdock'
    a_digest = 'sha256:' + 'a' * 64
    b_digest = 'sha256:' + 'b' * 64
    base_digest = 'sha256:' + 'c' * 64
    result = run_cppdock(['init'], load_fixture('cppdock-registry.json'),
        remote = {a_image + ':latest': image(a_image, ['a'], a_digest),
                  b_image + ':latest': image(b_image, ['b'], b_digest),
                  base_image + ':linux_x64':
                      image(base_image, ['c'], base_digest)})
    check(result.returncode == 0, '`cppdock init` failed with registries')
    main = result.config['platforms']['main']
    deps = main['deps']
    check(deps[0][0]['revision'] == a_digest,
          'docker dep not locked to the default_registry image')
    check(deps[1][0]['revision'] == b_digest,
          'docker dep not locked to its own registry image')
    check(main['base_image_revision'] == base_digest,
          'type default base image not locked in the default_registry')
    check(list(main)[:2] == ['type', 'base_image_revision'],
          'base image lock not written after "type"')

def test_registry_in_name():
    config = load_fixture('cppdock-registry.json')
    config['platforms']['main']['deps'][0][0]['name'] = 'ghcr.io/ricejasonf/a'
    result = run_cppdock(['init'], config)
    check(result.returncode != 0, 'docker dep name with a registry was accepted')

base_image_name = 'docker.io/ricejasonf/cppdock'
base_layers = layers_of('linux_x64')
base_lock_ref = lock_tag(base_image_name, base_layers)
base_local = {base_lock_ref: image(base_image_name, base_layers)}

# Make a config whose only dep is a docker dep locked to `revision`.
def docker_dep_config(revision):
    return {
        'cppdock': {'name': 'test_fetch'},
        'platforms': {'main': {
            'type': 'linux_x64',
            'base_image_revision': layers_lock(base_layers),
            'deps': [[{'name': 'ricejasonf/cppdock', 'type': 'docker',
                       'revision': revision}]]}}}

# Get the build commands of a run.
def builds(result):
    return [line.split() for line in result.log
            if line.startswith('buildx build')]

def test_lock_base_image():
    base_ref = base_image_name + ':linux_x64'
    base = image(base_image_name, base_layers)
    config = docker_dep_config(layers_lock(cppdock_layers))
    del config['platforms']['main']['base_image_revision']
    result = run_cppdock(['init'], config,
                         local = {base_ref: base, base_lock_ref: base})
    check(result.returncode == 0, '`cppdock init` failed to lock a base image')
    check(result.config['platforms']['main']['base_image_revision']
          == layers_lock(base_layers), 'base image not locked to its layers')
    check(pulled(result) == [], '`cppdock init` pulled a local base image')

def test_build_base_image():
    result = run_cppdock(['build', 'main'],
        docker_dep_config(layers_lock(cppdock_layers)),
        local = base_local,
        remote = {cppdock_lock_ref: image(cppdock_image, cppdock_layers)})
    check(result.returncode == 0, '`cppdock build` failed with a base lock')
    check(f'FROM {base_lock_ref}\n' in result.dockerfiles,
          'base image not built from the lock tag')
    check('COPY --from=cppdock_script cppdock' in result.dockerfiles,
          'base image does not copy the running script')
    commands = builds(result)
    check(len(commands) == 2 and
          all('--pull=never' in command for command in commands),
          'generated builds may pull')
    check(any(x.startswith('--build-context=cppdock_script=')
              for x in commands[0]),
          'base build has no cppdock_script context')

def test_build_base_image_mismatch():
    result = run_cppdock(['build', 'main'],
        docker_dep_config(layers_lock(cppdock_layers)),
        local = {base_lock_ref: image(base_image_name, layers_of('other'))})
    check(result.returncode != 0,
          '`cppdock build` accepted a base image with other layers')
    check(result.dockerfiles == '', 'built after a failed base image check')

# Make a config with an image platform built from a locked docker dep.
def image_config():
    return {
        'cppdock': {'name': 'test_image'},
        'platforms': {'img': {
            'type': 'image',
            'dockerfile': 'Dockerfile',
            'push_tag': 'ricejasonf/img',
            'deps': [[{'name': 'ricejasonf/cppdock', 'type': 'docker',
                       'build_arg': 'BASE',
                       'revision': layers_lock(cppdock_layers)}]]}}}

def test_release_image():
    result = run_cppdock(['release', 'img'], image_config(),
        local = {cppdock_lock_ref: image(cppdock_image, cppdock_layers)},
        files = {'Dockerfile': 'ARG BASE\nFROM ${BASE}\n'})
    check(result.returncode == 0, '`cppdock release` failed for an image')
    commands = builds(result)
    check(len(commands) == 1, 'image release ran other builds')
    check(f'--build-arg=BASE={cppdock_lock_ref}' in commands[0]
          and '--pull=never' in commands[0],
          'image not built from its locked dep without pulling')
    check(result.dockerfiles == 'ARG BASE\nFROM ${BASE}\n',
          'image not built from its Dockerfile')
    released = lock_tag('docker.io/ricejasonf/img', ['sha256:test_image-img'])
    check({'docker.io/ricejasonf/img', released} <= result.local,
          'image not tagged with its push tag and layers tag')

def test_release_no_build():
    released = lock_tag('docker.io/ricejasonf/img', ['sha256:test_image-img'])
    result = run_cppdock(['release', '--push', '--no-build', 'img'],
        image_config(),
        local = {'test_image-img': image('test_image-img',
                                         ['sha256:test_image-img'])})
    check(result.returncode == 0, '`cppdock release --no-build` failed')
    check(builds(result) == [] and pulled(result) == [],
          '`cppdock release --no-build` built or pulled')
    check({'docker.io/ricejasonf/img', released} <= result.remote,
          'release image not pushed with its push tag and layers tag')

def test_release_no_build_missing():
    result = run_cppdock(['release', '--no-build', 'img'], image_config())
    check(result.returncode != 0 and 'does not exist' in result.output,
          '`cppdock release --no-build` accepted a missing release image')

def test_image_dep_without_build_arg():
    config = image_config()
    del config['platforms']['img']['deps'][0][0]['build_arg']
    result = run_cppdock(['build', 'img'], config)
    check(result.returncode != 0, 'image dep without a build_arg accepted')

def test_dev_image():
    result = run_cppdock(['dev', 'img'], image_config())
    check(result.returncode != 0 and 'is an image' in result.output,
          '`cppdock dev` accepted an image platform')

def test_build_fetch():
    result = run_cppdock(['build', 'main'],
        docker_dep_config(layers_lock(cppdock_layers)),
        local = base_local,
        remote = {cppdock_lock_ref: image(cppdock_image, cppdock_layers)})
    check(result.returncode == 0, '`cppdock build` failed to fetch a dep')
    check(pulled(result) == [cppdock_lock_ref],
          '`cppdock build` did not pull only the lock tag')
    check(f'FROM {cppdock_lock_ref} AS' in result.dockerfiles,
          'build stage does not use the lock tag')

def test_build_fetch_by_tag():
    result = run_cppdock(['build', 'main'],
        docker_dep_config(layers_lock(cppdock_layers)),
        local = base_local,
        remote = {cppdock_image + ':latest':
            image(cppdock_image, cppdock_layers, cppdock_digest)})
    check(result.returncode == 0, '`cppdock build` did not fall back to the tag')
    check(pulled(result) == [cppdock_lock_ref, cppdock_image + ':latest'],
          '`cppdock build` did not try the lock tag and then the tag')
    check(cppdock_lock_ref in result.local,
          'fallback image not tagged with its layers lock')
    check(f'FROM {cppdock_lock_ref} AS' in result.dockerfiles,
          'build stage does not use the lock tag')

def test_build_fetch_by_tag_mismatch():
    result = run_cppdock(['build', 'main'],
        docker_dep_config(layers_lock(cppdock_layers)),
        local = base_local,
        remote = {cppdock_image + ':latest':
            image(cppdock_image, layers_of('newer'), cppdock_digest)})
    check(result.returncode != 0,
          '`cppdock build` accepted a tag with other layers')
    check(f'the registry has no {cppdock_lock_ref}' in result.output,
          'error does not say the lock tag is missing from the registry')

def test_build_digest():
    digest_ref = f'{cppdock_image}@{cppdock_digest}'
    result = run_cppdock(['build', 'main'], docker_dep_config(cppdock_digest),
        local = base_local,
        remote = {digest_ref:
            image(cppdock_image, cppdock_layers, cppdock_digest)})
    check(result.returncode == 0, '`cppdock build` failed with a digest lock')
    check(pulled(result) == [digest_ref], 'digest lock not pulled by digest')
    check(f'FROM {digest_ref} AS' in result.dockerfiles,
          'build stage does not use the digest')

def test_build_verify():
    result = run_cppdock(['build', 'main'],
        docker_dep_config(layers_lock(cppdock_layers)),
        local = base_local |
            {cppdock_lock_ref: image(cppdock_image, layers_of('other'))})
    check(result.returncode != 0,
          '`cppdock build` accepted an image with other layers')
    check(pulled(result) == [], '`cppdock build` pulled an image that is local')
    check(result.dockerfiles.count('FROM') == 1,
          '`cppdock build` built the deps image after a failed check')

test_lock_digest()
test_lock_layers()
test_lock_local()
test_lock_unreleased()
test_lock_stale_digest()
test_registry()
test_registry_in_name()
test_build_fetch()
test_build_fetch_by_tag()
test_build_fetch_by_tag_mismatch()
test_build_digest()
test_build_verify()
test_lock_base_image()
test_build_base_image()
test_build_base_image_mismatch()
test_release_image()
test_release_no_build()
test_release_no_build_missing()
test_image_dep_without_build_arg()
test_dev_image()
print('PASS')
