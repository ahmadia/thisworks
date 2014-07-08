"""
An IPython extension for specifying requirements
"""
import os
import sys
import socket
import time
from subprocess import Popen, PIPE, STDOUT
from itertools import dropwhile
from IPython.core.magic import magics_class, cell_magic, Magics

from IPython.display import display, Javascript

HASHSTACK_TEMPLATE=\
"""
extends:
 - name: hashstack
   urls: ['https://github.com/hashdist/hashstack.git']
   key: 'git:{git_id}'
   file: {platform}.yaml
"""

REDIRECT_TEMPLATE = """
// disable 'unsaved changes' dialog
window.onbeforeunload = function () {{}};
window.location = "{url}";
"""


def buffer_output(process):
    """Buffer the output of a Popen object to sys.stdout."""
    # show stdout as it comes
    while process.poll() is None:
        line = process.stdout.readline().decode('utf8', 'replace')
        sys.stdout.write(line)
        sys.stdout.flush()

    # finish off everything else
    remaining = process.stdout.read().decode('utf8', 'replace')
    if remaining:
        sys.stdout.write(remaining)
        sys.stdout.flush()


def call_buffered(cmd, **kwargs):
    """Call a subprocess and buffer its output to sys.stdout."""

    process = Popen(cmd, stdout=PIPE, stderr=STDOUT, **kwargs)
    buffer_output(process)

    if process.returncode != 0:
        raise Exception("%s failed with status %i" % (cmd[0], process.returncode))


def assemble_hashstack(command, profile_contents):
    """Convert friendly thisworks format to hashstack profile"""

    if command.startswith('hashstack/'):
        git_id = command.split('hashstack/')[1].rstrip()
    else:
        raise Exception("Unknown using command: ", command)

    platform = sys.platform                            
    profile_header = HASHSTACK_TEMPLATE.format(git_id=git_id, platform=platform)
    return profile_header.splitlines() + profile_contents


def transform_using(profile_contents):
    """Detect if first line of content is using:

    If so, return corresponding assembler
    """

    empty_lines = lambda x: x.strip()==''
    non_empty_lines = dropwhile(empty_lines, profile_contents)
    first_line = non_empty_lines.next().lstrip()
    if first_line.startswith('using'):
        # dispatch to other build profile providers here
        command = first_line.split('using')[1].lstrip().split(':')[1].lstrip()
        profile_contents = assemble_hashstack(command, list(non_empty_lines))
    return profile_contents

def random_port():
    """A random available port."""
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def wait_for_port(ip, port, timeout=2):
    """wait for a peer to show up at a port"""
    tic = time.time()
    while time.time() - tic < timeout:
        try:
            socket.create_connection((ip, port))
        except socket.error:
            time.sleep(0.1)
        else:
            return
    raise Exception("Notebook never seemed to start.")


@magics_class
class ThisWorks(Magics):



    @cell_magic
    def thisworks(self, line, cell):
        """Specify requirements for a notebook.
        
        Usage:
        
            %%thisworks notebook_name

            hashdist: stuff

        """
        if os.environ.get('THISWORKS', False):
            print("You are currently in a thisworks profile")
            return

        notebook_name = line.strip()
        if notebook_name:
            profile_name = notebook_name.rstrip('.ipynb')
        if not notebook_name:
            profile_name = 'this_works'

        profile_contents = cell.splitlines()
        profile_contents = transform_using(profile_contents)

        with open(profile_name + ".yaml", "w") as file:
            file.write('\n'.join(profile_contents))

        call_buffered(["hit", "build", profile_name + ".yaml"])
        ipython_path = os.path.join(profile_name, 'bin', 'ipython')
        port = random_port()
        ipython_cmd = [ipython_path, "notebook", os.getcwd(),
            '--no-browser', '--port=%i' % port, '--ip=localhost',
        ]
        print("calling %s" % ' '.join(ipython_cmd))
        env = os.environ.copy()
        env['THISWORKS'] = '1'
        ipython_process = Popen(ipython_cmd, stdout=PIPE, stderr=STDOUT, env=env)
        wait_for_port('localhost', port)
        url = "http://localhost:%i/notebooks/%s" % (port, notebook_name)
        display(Javascript(REDIRECT_TEMPLATE.format(url=url)))
        buffer_output(ipython_process)


def load_ipython_extension(ipython):
    ipython.register_magics(ThisWorks)
