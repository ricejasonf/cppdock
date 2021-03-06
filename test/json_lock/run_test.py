# TODO
# call `cppdock init` in this working dir
# test that json file is the same except for specifying revisions in each dep
# The dep with the hardcoded revision should NOT change

import os
import subprocess
import sys
import json

expected_revision_boosthana = 'd9da8776aa1142c0f92a38d49829ae5c3e86c7bc'

def start():

    p = subprocess.Popen(['cppdock', 'init'], stdin=subprocess.PIPE)
    out, err = p.communicate('')
    if p.returncode != 0:
        print """
        FAILURE
        """

    stream = file('cppdock.json', 'r')
    config = json.load(stream)

    result_revision_boosthana = config['platforms']['my_emscripten']['deps'][1][0]['revision']
    if not result_revision_boosthana == expected_revision_boosthana:
        raise ValueError('Boosthana locked revision changed.')

    platforms = config['platforms'].items()
    for platform, settings in platforms:
        for stage in settings['deps']:
            for item in stage:
                if 'revision' in item:
                    continue
                else:
                    raise ValueError('revision not added')

start()
