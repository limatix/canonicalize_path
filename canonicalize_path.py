"""This module exists to provide improved path canonicalization
Normally we can use os.path.realpath() to canonicalize paths, but
in some cases -- especially with synchronized shares -- there 
is a better canonical form. 

os.path.realpath eliminates symbolic links, but in some cases these
symbolic links are used not so much to reference an external location
but to define a canonical location. 

If those links (in canonical form) are entered in the canon_override
dictionary, below, then they will be replaced by the canonical 
replacements specified.

Suggested import:

try: 
   from canonicalize_path import canonicalize_path
   path
except ImportError:
   from os.path import realpath as canonicalize_path
   pass
"""

import sys
import os.path

canon_override={  # don't include excess path separators 
    "/sata4/databrowse": "/databrowse",
    "/sataa/databrowse": "/databrowse",
    "/home/databrowse":  "/databrowse",
    "/satas/databrowse": "/databrowse",
    "/home/dataawareness": "/dataawareness",
    "/satas/secbrowse":  "/secbrowse",
}


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

