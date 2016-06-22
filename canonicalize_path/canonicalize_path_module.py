import sys
import os.path

try: 
    from pkg_resources import resource_string
    pass
except:
    resource_string=None
    sys.stderr.write("canonicalize_path_module: Error importing pkg_resources (is package properly installed?)\n")
    pass

canon_override={}

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
    __install_prefix__=resource_string(__name__, 'install_prefix.txt').decode('utf-8')
    pass
except (IOError, TypeError): 
    sys.stderr.write("canonicalize_path_module: error reading install_prefix.txt. Assuming /usr/local.\n")
    __install_prefix__="/usr/local"
    pass

#if __install_prefix__=="/usr": 
#    config_dir='/etc/canonicalize_path'
#    pass
#else:
config_dir=os.path.join(__install_prefix__,"etc","canonicalize_path")


try: 
    canonical_paths_conf=resource_string(__name__, 'canonical_paths.conf').decode('utf-8')
    exec(u'canon_override='+canonical_paths_conf)
    pass
except (IOError,TypeError):
    sys.stderr.write("canonicalize_path_module: Error reading internal config file %s.\n" % ( "canonical_paths.conf"))
    pass

try: 
    canonical_paths=open(os.path.join(config_dir,"canonical_paths.conf"),"rb")
    exec(u'canon_override.update('+canonical_paths.read().decode('utf-8')+')')
    canonical_paths.close()
    pass
except (IOError,NameError):
    # No config file found
    #sys.stderr.write("canonicalize_path_module: Error reading config file %s.\n" % ( os.path.join(config_dir,"canonical_paths.conf")))
    pass

    

def canonicalize_relpath(contextdir,relpath):
    # given a path relpath, which may be relative to contextdir
    # determine the canonical path to this file
    if not os.path.isabs(relpath):
        abspath=os.path.join(contextdir,relpath)
        pass
    else:
        abspath=relpath
        pass
    return canonicalize_path(abspath)

def canonicalize_filelist(contextdir,filelist):
    # in-place canonicalize each entry in filelist
    # assume non-absolute paths are relative to contextdir

    for count in range(len(filelist)):
        filelist[count]=canonicalize_relpath(contextdir,filelist[count])
        pass
    pass



def rel_or_abs_path(contextdir,destfile,maxdots=1):
    # Determine the relative or absolute path to a known destination file starting from contextdir
    # if there are more than maxdots ".." entries at the start of the relative path, 
    # use the absolute path instead
    # NOTE: Use of this routine should be avoided because the maxdots 
    # method of counting parents is dodgy at best

    canonpath=canonicalize_path(destfile)
    relpath=relative_path_to(contextdir,canonpath)

    relpathsplit=pathsplit(relpath)
    
    gotnondots=False

    if len(relpathsplit) >= maxdots+1:
        for cnt in range(maxdots+1):
            if relpathsplit[cnt]!="..":
                gotnondots=True
                pass
            pass
        if not gotnondots: 
            # enough ".."s at start... use absolute path
            usepath=canonpath
            pass
        else: 
            usepath=relpath
            pass
        pass
    else: 
        usepath=relpath
        pass
    return usepath



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
    
    relpath=os.path.join(*relpath_split)
    return relpath
