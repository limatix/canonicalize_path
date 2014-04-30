
from pkg_resources import resource_string

import sys
import os.path

#canon_override={  # don't include excess path separators 
#    "/sata4/databrowse": "/databrowse",
#    "/sataa/databrowse": "/databrowse",
#    "/home/databrowse":  "/databrowse",
#    "/satas/databrowse": "/databrowse",
#    "/home/dataawareness": "/dataawareness",
#    "/satas/secbrowse":  "/secbrowse",
#}

# read canon_override from config files 
# $PREFIX/etc/canonicalize_path/canonical_paths.conf 
# and $PREFIX/etc/canonicalize_path/canonical_paths_local.conf 

__install_prefix__=resource_string(__name__, 'install_prefix.txt')

if __install_prefix__=="/usr": 
    config_dir='/etc/canonicalize_path'
    pass
else:
    config_dir=os.path.join(__install_prefix__,"etc","canonicalize_path")
    pass



canonical_paths=file(os.path.join(config_dir,"canonical_paths.conf"))
exec(u'canon_override='+canonical_paths.read().decode('utf-8'))
canonical_paths.close()

try: 
    canonical_paths_local=file(os.path.join(config_dir,"canonical_paths_local.conf"))
    exec(u'canon_override.update('+canonical_paths_local.read().decode('utf-8')+')')
    canonical_paths_local.close()
    pass
except IOError:
    pass
    

def pathsplit(path,lastsplit=None): 
    """portable equivalent for os string.split("/")... 
    lastsplit parameter for INTERNAL USE ONLY
    Can reconstruct with os.path.join(*pathsplit(path))"""

    split=os.path.split(path)
    if split==lastsplit: 
        return []
        pass
    pathlist=pathsplit(split[0],split)
    if len(pathlist)==0: 
        pathlist.append(split[0])
        pass
        
    pathlist.append(split[1])
    return pathlist
    


canon_override_db={} # dictionary indexed by first elements, 
# of dictionaries indexed by second elements, etc. 
# "None" element in dictionary indicates replacement


for key in canon_override:
    pathels = pathsplit(key)
    dbpos=canon_override_db

    for pathel in pathels: 
        if pathel not in dbpos:
            dbpos[pathel]={}
            pass
        dbpos=dbpos[pathel]
        pass
    dbpos[None]=canon_override[key]
    pass
    

def translate_prefix(dbpos,pathels):
    # sys.stderr.write("pathels=%s\n" % pathels)
    if len(pathels) > 0 and pathels[0] in dbpos:
        replpath=translate_prefix(dbpos[pathels[0]],pathels[1:])
        if replpath is not None:
            return replpath
        pass
    if None in dbpos: 
        newpath = [dbpos[None]]
        newpath.extend(pathels)
        return newpath
    else : 
        return None
    pass


def canonicalize_path(path):
    """Canonicalize the given path. Like os.path.realpath()x, but 
    with prefix substitutions according to the mapping at the 
    top of canoncalize_path.py
    """

    pycanon=os.path.realpath(path) # os.path.abspath(path))

    # split path apart
    pycanonels=pathsplit(pycanon)
    
    dbpos=canon_override_db

    trans=translate_prefix(dbpos,pycanonels)

    if trans is None:
        trans=pycanonels
        pass
        

    return os.path.join(*trans)

