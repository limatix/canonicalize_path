# Canonical xlinks
#
# * Canonical xlinks can be relative, but they can only be relative 
#   to the containing file, not the source element
# * They consist of three parts: 
#     1. File or web path (relative or absolute) -- fully canonical requires an absolute path 
#     2. namespace mapping
#     3. xpath
#

# To make things canonical, the xpath is constrained. 
# It uses the tag_index_paths logic of canonicalize_xpath_module
# to define unique and repeatable constraints to identify
# an element. 
# 
# These paths are only properly canonical so long as tag_index_paths
# is consistent (!) so it is generally only safe to rely on them being 
# canonical if you re-canonicalize them yourself

# Format:
#  /databrowse/path/to/file.xml#xpath({cn0=http://thermal.cnde.iastate.edu/datacollect,cn1=http://thermal.cnde.iastate.edu/checklist}cn0:summary[@cn1:foo='bar']/cn1:clinfo)

# Namespace mapping
# -----------------
# For an xpath to be canonical, it has to have a predictable namespace
# mapping, and the namespace mapping has to be considered part of the 
# xpath. Fortunately the xlink standard allows namespace mappings to 
# be provided alongside the xpath
# 
# Namespace prefixes are defined in order, cn1, cn2, etc. (as many as
# necessary). The order corresponds to the order that they are used 
# in the xpath: For each path segment, any namespace needed by 
# the tag name would be first, namespaces referenced in any 
# bracket constraint would follow. Namespaces referenced in the next
# path segment would follow all of those from the previous segment. 
# If a namespace has already been referenced, we don't define 
# an additional prefix. 

def etxpath2xlink(context_etxpath,etxpath):
    # Note: any relative etxpath required to get to the root
    # of the context file will be truncated!
    
    
    # First, canonicalize it
    if not(etxpath_isabs(etxpath)):
        # relative path -- must join with context
        assert(context_etxpath is not None)
        canon_etxpath=canonicalize_xpath_module.canonicalize_etxpath(canonical_etxpath_join(context_etxpath,etxpath))
        pass
    else:         
        # absolute path
        canon_etxpath=canonicalize_xpath_module.canonicalize_etxpath(etxpath)
        pass
    
    # now break out the file portion from the xpath
    (targetfile,targetetxpath)=canonicalize_xpath_module.canonical_etxpath_break_out_file(canon_etxpath)
    
    if not(etxpath_isabs(etxpath)):
        # relative path -- must define contextfile,
        # then determine targetpath relative to contextfile
        (contextfile,contextetxpath)=canonicalize_xpath_module.canonical_etxpath_break_out_file(canonicalize_xpath_module.canonicalize_path(context_etxpath))
        targetpath=canonicalize_path_module.relative_path_to(os.path.split(contextfile)[0],targetfile)

        if targetpath==os.path.split(contextfile)[1]:
            # target file is the same file as contextfile
            targetpath=""  # will append hash+xpath
            pass
        pass
    else: 
        # absolute path -- targetpath = targefile
        targetpath=targetfile
        pass

    
    # now need to break down targetextpath and transform it into a 
    # simple xpath + a namespace mapping

    # This is quite similar to canonicalize_xpath_module.etxpath2human()
    
    targetetxpathcomponents=canonical_etxpath_split(targetetxpath)

    buildrevnsmap=collections.OrderedDict() # reverse nsmap: mapping to namespace to prefix 
    buildpath=[]
    nextnsidx=0  # index of next "cn" namespace prefix to add 

    for pathentry in splitpath:
        matchobj=canonicalize_xpath_module.xpath_clarkcvt_match_obj.match(pathentry)
        # group(1) is Clark prefix, group(2) is tag, group(3) is primary constraint, group(4) is secondary constraint
        clarkpfx=matchobj.group(1)
        
        if clarkpfx is not None:
            if clarkpfx[1:-1] not in buildrevnsmap:
                buildrevnsmap[clarkpfx[1:-1]]="cn%d" % (nextnsidx)
                nextnsidx+=1
                pass
            newpfx=buildrevnsmap[clarkpfx[1:-1]]+":"
            pass
        else:
            # null namespace
            # !!!*** bug???: What happens if in the context of where we
            # place this xlink, there is a default namespace defined?
            # Is it then impossible to refer to tags in the default
            # namespace?  ...  Answer: No. xpath doesn't have the 
            # concept of a default namespace, so this problem does 
            # not occur. 
            newpfx=""
            pass
        newtag=matchobj.group(2)

        primconstraint=matchobj.group(3)

        newprim=""
        if primconstraint is not None:
            newprim+="["
                        # Iterate over elements of primconstraint
            for primconstraint_el_obj in re.finditer(canonicalize_xpath_module.xpath_primconstraint_match_re,primconstraint[1:-1]):
                # group(1) is arbitrary characters, group(2) is double-quoted strings, group(3) is single-quoted strings, group(4) is Clark notation
                if primconstraint_el_obj.group(4) is not None:
                    const_clarkpfx=primconstraint_el_obj.group(4)
                    if const_clarkpfx[1:-1] not in buildrevnsmap:
                        buildrevnsmap[clarkpfx[1:-1]]="cn%d" % (nextnsidx)
                        nextnsidx+=1
                        pass

                    const_newpfx=buildrevnsmap[const_clarkpfx[1:-1]]+":"
                    newprim+=const_newpfx
                    pass
                else :
                    newprim+=primconstraint_el_obj.group(0) # attach everything
                    pass
                pass
            newprim+="]" # attach trailing close bracket
            pass
        secconstraint=matchobj.group(4)  # brackets surrounding a number, 
                                         # e.g. [8]
        if secconstraint is None: 
            secconstraint=""
            pass
        
        buildpath.append(newpfx+newtag+newprim+secconstraint)
        pass
    
    # xpath component is always absolute
    joinpath=canonical_etxpath_absjoin(*buildpath)
    
    # buildrevnsmap is an ordered dictionary so it is already sorted.
    nsmaplist=[ (nspre,url) for (url,nspre) in buildrevnsmap.items()]

    nsmapstrings=[ "xmlns(%s=%s)" % (nspre,url) for (nspre,url) in nsmaplist]
    
    xlink="%s#%sxpath(%s)" % (targetpath,"".join(nsmapstrings),joinpath)
    
    return xlink
