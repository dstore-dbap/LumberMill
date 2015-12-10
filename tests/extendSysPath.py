module_dirs = {'input': {},
               'parser': {},
               'modifier': {},
               'output': {},
               'misc': {}}

import sys
import os

# Expand the include path to our libs and modules.
# TODO: Check for problems with similar named modules in 
# different module directories.
pathname = os.path.abspath(__file__)
pathname = pathname[:pathname.rfind("/")]
sys.path.append(pathname+"/../gambolputty")
[sys.path.append(pathname+"/../gambolputty/"+mod_dir) for mod_dir in module_dirs]