
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

try: 
    __install_prefix__=resource_string(__name__, 'install_prefix.txt')
    pass
except IOError: 
    sys.stderr.write("canonicalize_path_module: error reading install_prefix.txt. Assuming /usr/local.\n")
    __install_prefix__="/usr/local"
    pass

if __install_prefix__=="/usr": 
    config_dir='/etc/canonicalize_path'
    pass
else:
    config_dir=os.path.join(__install_prefix__,"etc","canonicalize_path")
    pass



try: 
    canonical_paths=file(os.path.join(config_dir,"canonical_paths.conf"))
    exec(u'canon_override='+canonical_paths.read().decode('utf-8'))
    canonical_paths.close()
    pass
except IOError:
    sys.stderr.write("canonicalize_path_module: Error reading config file %s.\n" % ( os.path.join(config_dir,"canonical_paths.conf")))
    pass


try: 
    canonical_paths_local=file(os.path.join(config_dir,"canonical_paths_local.conf"))
    exec(u'canon_override.update('+canonical_paths_local.read().decode('utf-8')+')')
    canonical_paths_local.close()
    pass
except IOError:
    sys.stderr.write("canonicalize_path_module: Warning: No local config file %s.\n" % ( os.path.join(config_dir,"canonical_paths_local.conf")))
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

def relative_path_to(fromdir,tofile):
    fromdir=canonicalize_path(fromdir)
    tofile=canonicalize_path(tofile)
    
    if fromdir.endswith(os.path.sep):
        fromdir=fromdir[:-1]  # eliminate trailing '/', if present
        pass

    fromdir_split=pathsplit(fromdir)
    tofile_split=pathsplit(tofile)

    # Determine common prefix
    pos=0
    while pos < len(fromdir_split) and pos < len(tofile_split) and fromdir_split[pos]==tofile_split[pos]:
        pos+=1
        pass

    relpath_split=[]

    # convert path entries on 'from' side to '..'
    for entry in fromdir_split[pos:]:
        if len(entry) > 0: 
            relpath_split.append('..')
            pass
        pass

    # add path entries on 'to' side
    for entry in tofile_split[pos:]:
        if len(entry) > 0: 
            relpath_split.append(entry)
            pass
        pass
    
    relpath=os.path.join(relpath_split)
    return relpath
