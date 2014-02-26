"""
An IPython extension for specifying requirements
"""
import os
from subprocess import check_call
from IPython.core.magic import magics_class, cell_magic, Magics

@magics_class
class ThisWorks(Magics):

    @cell_magic
    def thisworks(self, line, cell):
        """Specify requirements for a notebook.
        
        Usage:
        
            %thisworks profile_name

        """
        profile_name = line
        if not profile_name:
            profile_name = 'this_works'
        profile_contents = cell

        with open(profile_name + ".yaml", "w") as file:
            file.write(profile_contents)
    
        check_call(["hit","build",profile_name+".yaml"])
        ipython_path = os.path.join(profile_name, 'bin', 'ipython')
        check_call([ipython_path, "notebook"])


def load_ipython_extension(ipython):
    ipython.register_magics(ThisWorks)