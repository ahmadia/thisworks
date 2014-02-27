"""
An IPython extension for specifying requirements
"""
import os
import sys
from subprocess import check_call
from itertools import dropwhile
from IPython.core.magic import magics_class, cell_magic, Magics

HASHSTACK_TEMPLATE=\
"""
extends:
 - name: hashstack
   urls: ['https://github.com/hashdist/hashstack.git']
   key: 'git:{git_id}'
   file: {platform}.yaml
"""


def assemble_hashstack(command, profile_contents):
    """Convert friendly thisworks format to hashstack profile"""

    if command.startswith('hashstack/'):
        git_id = command.lstrip('hashstack/').rstrip()
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
        command = first_line.lstrip('using').lstrip().lstrip(':').lstrip()
        profile_contents = assemble_hashstack(command, list(non_empty_lines))
    return profile_contents

@magics_class
class ThisWorks(Magics):



    @cell_magic
    def thisworks(self, line, cell):
        """Specify requirements for a notebook.
        
        Usage:
        
            %thisworks profile_name

        """
        notebook_name = line.strip()
        if notebook_name:
            profile_name = notebook_name.rstrip('.ipynb')
        if not notebook_name:
            profile_name = 'this_works'

        profile_contents = cell.splitlines()
        profile_contents = transform_using(profile_contents)

        with open(profile_name + ".yaml", "w") as file:
            file.write('\n'.join(profile_contents))
    
        check_call(["hit","build",profile_name+".yaml"])
        ipython_path = os.path.join(profile_name, 'bin', 'ipython')
        print "calling", ipython_path, "notebook", notebook_name
        check_call([ipython_path, "notebook", notebook_name])


def load_ipython_extension(ipython):
    ipython.register_magics(ThisWorks)