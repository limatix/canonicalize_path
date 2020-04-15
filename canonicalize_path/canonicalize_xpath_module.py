import sys
import os.path
import string
import re
import copy


try: 
    import builtins  # python3
    pass
except ImportError: 
    import __builtin__ as builtins # python2
    pass


if not hasattr(builtins,"basestring"):
    basestring=str  # python3
    pass
try:
    import collections.abc as collections_abc  # python 3.3 and above
    pass

except ImportError:
    import collections as collections_abc # < python 3.3
    pass

try:
    from pkg_resources import resource_string
    pass
except:
    resource_string=None
    sys.stderr.write("canonicalize_xpath_module: Error importing pkg_resources (is package properly installed?)\n")
    pass



from .canonicalize_path_module import canonicalize_path
from .canonicalize_path_module import pathsplit

###***!!! Bug: This module doesn't explicitly define 
### filename paths as distinct from URLs, so 
### it will probably fail on Windows.
###  -- Need to use urllib.pathname2url()
###     and urllib.url2pathname() to convert
###     back and forth


try: 
    from lxml import etree
    pass
except ImportError: 
    pass
    
try: 
    __install_prefix__=resource_string(__name__, 'install_prefix.txt').decode('utf-8')
    pass
except (IOError,TypeError): 
    sys.stderr.write("canonicalize_xpath_module: error reading install_prefix.txt. Assuming /usr/local.\n")
    __install_prefix__="/usr/local"
    pass



#if __install_prefix__=="/usr": 
#    config_dir='/etc/canonicalize_path'
#    pass
#else:
config_dir=os.path.join(__install_prefix__,"etc","canonicalize_path")

DBDIR="{http://limatix.org/databrowse/dir}dir"
DBFILE="{http://limatix.org/databrowse/dir}file"


# Canonical ETxpaths are only properly canonical so long as tag_index_paths
# is consistent (!) so it is generally only safe to rely on them being 
# canonical if you re-canonicalize them yourself

# Example tag_index_paths.conf:
# {
#   "{http://limatix.org/databrowse/dir}dir":  "@name",
#   "{http://limatix.org/databrowse/dir}file": "@basename",
#   "{http://limatix.org/datacollect}measurement": "measnum",
#
# }


try: 
    tag_index_paths_conf_str=resource_string(__name__, 'tag_index_paths.conf').decode('utf-8')
    exec(u'tag_index_paths='+tag_index_paths_conf_str)
    pass
except (IOError,TypeError):
    sys.stderr.write("canonicalize_path_module: Error reading internal config file %s.\n" % ( "tag_index_paths.conf"))
    pass

try:
    tag_index_paths_conf=open(os.path.join(config_dir,"tag_index_paths.conf"),"rb")
    exec(u'tag_index_paths.update('+tag_index_paths_conf.read().decode('utf-8')+')')
    tag_index_paths_conf.close()
    pass
except (IOError,NameError):
    #sys.stderr.write("canonicalize_xpath_module: Error reading config file %s.\n" % ( os.path.join(config_dir,"tag_index_paths.conf")))
    pass



def string_to_etxpath_expression(strval):
    """Converts a string into a valid ETXPath expression.
    strval should either be a string or an Element (in which case
    we operate on Element.text). 
    
    This quotes the string, and deals with the weird case of using
    concat() if it contains both single and double quotes. 
    """

    if not isinstance(strval,basestring):
        # Did we get a node?
        if hasattr(strval,"tag"):
            strval=strval.text
            pass
        # Did we get a length-1 node-set?
        elif isinstance(strval,collections_abc.Sequence) and len(strval)==1:
            strval=strval[0].text
            pass 
        else: 
            raise ValueError("Invalid parameter value (%s) for converting tag into an XPath matching expression: Must be a node, length-one node-set, or string. See also tag_index_paths.conf and tag_index_paths_local.conf" % (str(strval)))
        pass
        
    
    if strval.find("\"") < 0:
        return "\""+strval+"\"" # use double quotes
    
    if strval.find("\'") < 0:
        return "\'"+strval+"\'" # use single quotes
    
    # use Concat with double quotes so single quotes are OK

    splitstr=strval.split("\"") # split into segments that don't have double quotes
    
    quotedsplitstr=["\""+component+"\"" for component in splitstr] # Put quotes around each segment
    return "concat(%s)" % (",'\"',".join(quotedsplitstr)) # Join with double quotes and return in a concat expression

    

def getelementetxpath(doc,element,root=None,tag_index_paths_override=None):
    # returns full Clark notation xpath (see ETXPath)
    # with leading slash and root element defined 
    # relative to this document, not the filesystem!

    # if root is provided, paths will be relative to this root
    # instead of doc.getroot() (and doc will not be used)

    if root is None:
        root=doc.getroot()
        pass

    parent=element.getparent()
    if parent is None or root is element:
        # at root 
        assert(root is element)
        pathel="/%s[1]" % (element.tag)
        return pathel
    else :
        # recursive call to get earlier path components
        pathprefix=getelementetxpath(None,parent,root,tag_index_paths_override=tag_index_paths_override)

        if tag_index_paths_override is None:
            tag_index_paths_use=tag_index_paths
            pass
        else: 
            tag_index_paths_use=copy.deepcopy(tag_index_paths)
            tag_index_paths_use.update(tag_index_paths_override)
            pass

        #sys.stderr.write("element.tag=%s; tag_index_paths_use=%s\n" % (element.tag,tag_index_paths_use))

        if element.tag in tag_index_paths_use:
            #sys.stderr.write("Foundit!\n")
            indices=tag_index_paths_use[element.tag]  # get index xpath expression for identifying this element
            
            if isinstance(indices,basestring):
                # if only one index location is provided...
                indices=(indices,)
                pass
            
            indexstr=""

            for index in indices: 
                # now extract the value of this expression for our element
                # print "index=%s" % (index)
                ETXindexval=etree.ETXPath(index) # if etree is None here you need to install python-lxml
                indexval=ETXindexval(element) # perform xpath lookup
                #sys.stderr.write("indexval=%s\n" % (unicode(indexval)))
                #sys.stderr.write("element=%s\n" % (etree.tostring(element)))
                if not isinstance(indexval,basestring):
                    # Did we get a node?
                    if hasattr(indexval,"tag"):
                        indexval=indexval.text
                        pass
                    # Did we get a length-1 node-set, strings, etc.?
                    elif isinstance(indexval,collections_abc.Sequence) and len(indexval)==1:
                        if isinstance(indexval[0],basestring):
                            indexval=indexval[0]
                            pass
                        else:
                            assert(hasattr(indexval[0],"tag")) # should be an element 
                            indexval=indexval[0].text
                            pass
                        pass 
                    elif isinstance(indexval,collections_abc.Sequence) and len(indexval) > 1:
                        raise ValueError("Got multiple nodes searching for index element %s in " % (index))
                    if indexval is None:
                        indexval=""
                        pass
                    pass
                if len(indexval) > 0:  # if we found a suitable non-empty string
                    indexvalexpr=string_to_etxpath_expression(indexval)  
                    indexstr="[%s=%s]" % (index,indexvalexpr)
                    # print "indexstr=%s" % (indexstr)
                    # No need to go on. We found a suitable index
                    break
                pass
            pass
        else :
            indexstr=""
            pass
        #sys.stderr.write("element.tag=%s\nindexstr=%s\n" % (element.tag,indexstr))
        if "Comment" in type(element).__name__:
            # This is a comment node
            
            ETXindex=etree.ETXPath("comment()")  # if etree is None here you need to install python-lxml
            comment_siblings = ETXindex(parent)

            elnum=[ i for i in range(len(comment_siblings)) if comment_siblings[i] is element ][0]+1
            
            pathel="comment()[%d]" % (elnum)

            pass
        else:
            
            ETXindex=etree.ETXPath("%s%s" % (element.tag,indexstr))  # if etree is None here you need to install python-lxml
            
            # Try this index on parent
            siblings=ETXindex(parent)
            elnum=[ i for i in range(len(siblings)) if siblings[i] is element ][0]+1

            pathel="%s%s[%d]" % (element.tag,indexstr,elnum)
            pass

        return "%s/%s" % (pathprefix,pathel)
    pass
 
# (@?) optional this-is-an-attribute
# ({[^}]+})?     Optional Clark notation
# ([^[\]{}@/]+)      Tag name
# (?:([\[] ... []])([\[]\d+[]])?)?   Optional Constraint plus Optional Integer Constraint
# [^[\]"'{}]+     Constraint content no quotes or braces
# "[^"]*"         Double Quoted string
# '[^']*'         Single quoted string
# [{][^{}]*[}]    Clark notation string
# (?:(?:[^[\]"'{}]+)|(?:"[^"]*")|(?:'[^']*')|(?:[{][^{}]*[}]))+  Constraint content w/quotes and/or Clark notation
xpath_clarkcvt_match_re=r"""(@?)({[^}]+})?([^[\]{}@/]+)(?:([\[](?:(?:[^[\]"'{}]+)|(?:"[^"]*")|(?:'[^']*')|(?:[{][^{}]*[}]))+[]])([\[]\d+[]])?)?"""
xpath_clarkcvt_match_obj=re.compile(xpath_clarkcvt_match_re)

# xpath_primconstraint_match_re matches one element of the primary constraint, not including surrounding [] 
xpath_primconstraint_match_re=r"""([^[\]"'{}]+)|("[^"]*")|('[^']*')|([{][^{}]*[}])"""

# Above expressions also used by canonical_xlink_module.etxpath2xlink

def etxpath2human(etxpath,nsmap):
    # Convert an etxpath into a more human readable xpath using 
    # nsmap. Result may be a mixture of prefix- and Clark notation


    # reverse namespace mapping
    revnsmap=dict((url,nspre) for nspre,url in nsmap.items() if nspre is not None)

    # print("etxpath2human: %s; nsmap=%s" % (etxpath,str(nsmap)))
    
    splitpath=canonical_etxpath_split(etxpath)
    # print("etxpath2human: splitpath=%s" % (splitpath))

    buildpath=[]
    for pathentry in splitpath:
        # print("etxpath2human: pathentry=%s" % (pathentry))
        if len(pathentry)==0:
            # blank entry... indicates first entry of absolute path
            buildpath.append("")
            continue
        
        matchobj=xpath_clarkcvt_match_obj.match(pathentry)
        # group(1) is optional '@' group(2) is Clark prefix, group(3) is tag, group(4) is primary constraint, group(5) is secondary constraint
        optionalatsign=matchobj.group(1)
        clarkpfx=matchobj.group(2)
        newpfx=""
        if clarkpfx is not None:
            if clarkpfx[1:-1] in revnsmap:
                newpfx=revnsmap[clarkpfx[1:-1]]+":"
                pass
            else : 
                newpfx=clarkpfx
                pass
            pass
        
        newtag=matchobj.group(3)
        # print("newtag=",newtag)

        primconstraint=matchobj.group(4)
        newprim=""
        if primconstraint is not None:
            newprim+="["
            # Iterate over elements of primconstraint
            for primconstraint_el_obj in re.finditer(xpath_primconstraint_match_re,primconstraint[1:-1]):
                # group(1) is arbitrary characters, group(2) is double-quoted strings, group(3) is single-quoted strings, group(4) is Clark notation
                if primconstraint_el_obj.group(4) is not None:
                    const_clarkpfx=primconstraint_el_obj.group(4)
                    if const_clarkpfx[1:-1] in revnsmap:
                        const_newpfx=revnsmap[const_clarkpfx[1:-1]]+":"
                        pass
                    else : 
                        const_newpfx=const_clarkpfx
                        pass
                    newprim+=const_newpfx
                    pass
                else :
                    newprim+=primconstraint_el_obj.group(0) # attach everything
                    pass
                pass
            newprim+="]" # attach trailing close bracket
            pass
        #if newprim=="[1]":  # BUG: Culling this may not be correct if there are sibling elements with the same tag name or other constraints. For human viewing, it is certainly OK
        #    newprim=""
        #    pass
        
        secconstraint=matchobj.group(5)
        newsec=""
        #if secconstraint is not None and secconstraint != "[1]":
        #    # BUG: Culling the [1] may not be correct if there are sibling elements with the same tag name or other constraints. For human viewing, it is certainly OK
        if secconstraint is not None:
            newsec=secconstraint
            pass
        
        buildpath.append(optionalatsign+newpfx+newtag+newprim+newsec)
        pass

    joinpath=canonical_etxpath_join(*buildpath)

    # print("etxpath2human: joinpath=%s" % (joinpath))

    return joinpath



def getelementhumanxpath(doc,element,nsmap=None,root=None,tag_index_paths_override=None):
    # returns human-readable (to maximum extent possible!) xpath
    # with leading slash and root element defined relative to this
    # document, not the filesystem 
    # 
    # NOTE: Returned value may NOT be a valid XPath OR a valid ETXPath
    # because it may be mixed prefix and Clark notation

    # if root is provided, paths will be relative to this root
    # instead of doc.getroot() (and doc will not be used)

    # Merge namespace mappings

    if root is None: 
        root=doc.getroot()
        pass

    newnsmap=dict(root.nsmap)
    newnsmap.update(element.nsmap)
    if nsmap is not None: 
        newnsmap.update(nsmap)
        pass
    
    etxpath=getelementetxpath(None,element,root,tag_index_paths_override=tag_index_paths_override)
    
    return etxpath2human(etxpath,newnsmap)


def filepath_to_etxpath(canonical_filepath):
    """Convert a file path into a db:dir/db:file xpath.
    Suggested that you generally want to canonicalize filepath
    first (with canonicalize_path)"""

    #Split file path into components
    filecomponents=pathsplit(canonical_filepath)
    if not os.path.isdir(canonical_filepath):
        dircomponents=filecomponents[:-1]
        filecomponent=filecomponents[-1]
        pass
    else :
        dircomponents=filecomponents
        filecomponent=None
        pass

    # Convert each path component into an ETXPath query component 
    pathcomponents=["%s[@name=%s]" % (DBDIR,string_to_etxpath_expression(fc)) for fc in dircomponents if fc != "" and fc != "/"]

    # print "dircomponents=%s" % (dircomponents)
    
    if filecomponent is not None:
        pathcomponents.append("%s[@basename=%s]" % (DBFILE,string_to_etxpath_expression(filecomponent)))
        pass
        
    if os.path.isabs(canonical_filepath):
        pathcomponents.insert(0,'') # force leading slash after join
        pass

    filexpath="/".join(pathcomponents)
    
    return filexpath

def create_canonical_etxpath(filepath,doc,element):
    """Find a canonical absolute (Clark notation) xpath representation based 
       off the filesystem root for the specified element within
       doc. 

       filepath should be a relative or absolute path to doc.
       doc is the etree.ElementTree document containing element
       element is an XML etree.Element within doc
    """

    # print "Create_canonical_etxpath(%s,...)" % (filepath)
    canonical_filepath=canonicalize_path(filepath)

    if doc is not None:
        xpath=getelementetxpath(doc,element)
        pass
    else :
        xpath=""
        pass
    # print " -> \"%s\", \"%s\"" % (canonical_filepath,xpath)

    filexpath=filepath_to_etxpath(canonical_filepath)

    fullxpath=filexpath+xpath
    
    # print " -> %s" % (fullxpath)

    return fullxpath


# Only accepts reduced xpath from our canonical xpath generator
# (@?)           Optional at-sign
# ({[^}]+})?     Optional Clark notation
# ([^[\]/]+)      Tag name
# (?:([\[] ... []])([\[]\d+[]])?)?   Optional Constraint plus Optional Integer Constraint
# [^[\]"']+      Constraint content no quotes
# "[^"]*"         Double Quoted string
# '[^']*'         Single quoted string
# (?:(?:[^[\]"']+)|(?:"[^"]*")|(?:'[^']*'))+  Constraint content w/quotes
xpath_component_match_re=r"""(@?)({[^}]+})?([^[\]/]+)(?:([\[](?:(?:[^[\]"']+)|(?:"[^"]*")|(?:'[^']*'))+[]])([\[]\d+[]])?)?"""
xpath_component_match_obj=re.compile(xpath_component_match_re)
xpath_slashcomponent_match_obj=re.compile("/"+xpath_component_match_re)

def canonical_etxpath_split(fullxpath):
    """Split etxpath into individual xpath components
    Only accepts ximple paths and reduced xpath from our canonical 
    xpath generator, not full general XPath queries"""

    #     
    
    text=""
    components=[]

    fullxpath=fullxpath.strip()

    absolute=fullxpath[0]=='/'

    if not absolute:
        fullxpath="/"+fullxpath  # put leading slash for parsing        
        pass
    else:
        components.append("")  # blank leading component represents absolute path
        pass
    
    for matchobj in xpath_slashcomponent_match_obj.finditer(fullxpath):
        # for matchobj in re.finditer(r"""/({[^}]+})?([^[\]/]+)([\[](?:(?:[^[\]/"']+)|(?:"[^"]*")|(?:'[^']*'))+[]])([\[]\d+[]])?""",fullxpath):
        if matchobj is None: 
            raise SyntaxError("XPath parsing \"%s\" after \"%s\"." % (fullxpath,text))
        # group(1) is optional at-sign; group(2) is Clark prefix, group(3) is tag, group(4) is primary constraint, group(5) is secondary constraint
        match=matchobj.group(0)
        text+=match
        components.append(match[1:]) # append to path component list, but drop '/'
        pass

    return components

def canonical_etxpath_join(*components):
    # Does NOT supply additional leading "/" to make the path absolute
    return "/".join(components)    

def canonical_etxpath_absjoin(*components):
    # DOES  supply leading "/" to make the path absolute
    components=list(components)
    components.insert(0,"")
    # print components
    return "/".join(components)
    
# check format of primary constraint
# should be name="quotedstring" name='quotedstring'
# or name=concat("foo",...)
# name=             Prefix
# (?:  ... )        Main grouping of concatenation vs. no concat options
# (?:concat\(( ... )\)) Concatenation
# (?:[^)"']*)      Concatenation content no quotes
# (?:"([^"]*)")     Double quoted string
# (?:'([^']*)')     Single quoted string
# (?:([^)"']*)|(?:"[^"]*")|(?:'[^']*'))+  Concatenation content w/quotes
# (?:"([^"]*)")     Simple Double quoted string (no concatenation)
# (?:'([^']*)')     Simple Single quoted string (no concatenation)
constraint_match_re=r"""\[@name=(?:(?:concat\(((?:(?:[^)"']*)|(?:"[^"]*")|(?:'[^']*'))+)\))|(?:"([^"]*)")|(?:'([^']*)'))\]$"""
constraint_match_obj=re.compile(constraint_match_re)

constraint_filematch_re=r"""\[@basename=(?:(?:concat\(((?:(?:[^)"']*)|(?:"[^"]*")|(?:'[^']*'))+)\))|(?:"([^"]*)")|(?:'([^']*)'))\]$"""
constraint_filematch_obj=re.compile(constraint_filematch_re)



# (?:"([^"]*)")     Double quoted string
concat_match_re = r"""(?:"([^"]*)"),?"""


def canonical_etxpath_break_out_file(fullxpath):
    """Break out file path from xpath components of a canonical xpath
    Presumes the file portion covers the entire leading 
    sequence of dbdir:dir an dbdir:file elements
    returns (filepath, xpath within that file)"""
    
    components=canonical_etxpath_split(fullxpath)
    
    isdir=True

    if os.path.sep=="/":
        filepath="/"
        pass
    else:
        filepath=""
        pass
    
    xpath=""


    assert(components[0]=='') # absolute path
    
    compnum=1
    while isdir:
        component=components[compnum]
        # print components
        # print component
        matchobj=xpath_component_match_obj.match(component)
        (optionalatsign,clarkpfx,tag,primconstraint,secconstraint)=matchobj.groups()
        # print matchobj.groups()
        
        assert(optionalatsign=="")
        
        if (clarkpfx=="{http://limatix.org/databrowse/dir}" and
            (tag=="dir" or tag=="file") and (secconstraint is None or secconstraint=="[1]")):
            if tag=="dir":
                constraintmatch=constraint_match_obj.match(primconstraint)
                pass
            else : 
                constraintmatch=constraint_filematch_obj.match(primconstraint)
                isdir=False
                pass
            # print primconstraint
            # print constraintmatch
            if constraintmatch is not None:
                (concatconstraint,doublequoted,singlequoted)=constraintmatch.groups()
                if doublequoted is not None:
                    filepath=os.path.join(filepath,doublequoted)
                    pass
                elif singlequoted is not None:
                    filepath=os.path.join(filepath,singlequoted)
                    pass
                else: # concat 
                    assert(concatconstraint is not None)
                    # assemble concatconstraint
                    filepath=os.path.join(filepath,"".join([matchobj.group(1) for matchobj in re.finditer(concat_match_re,concatconstraint)]))
                    pass
                compnum+=1
                continue
            pass
        isdir=False
        pass
    
    if len(components) > compnum:
        xpath = "/"+ "/".join(components[compnum:])
        pass

    return (filepath,xpath)

def etxpath_isabs(xpath):
    """Returns TRUE if the xpath is absolute (leading /)"""
    if len(xpath)==0:
        return False
    return xpath[0]=='/'
    

def etxpath_resolve_dots(xpath):
    
    xpathsplit=canonical_etxpath_split(xpath)

    posn=0
    while posn < len(xpathsplit):
        # print "erd: xps=%s" % (unicode(xpathsplit))
        if xpathsplit[posn]==".":  
            del xpathsplit[posn]  # "." is just the same as its parent element
            # no increment
            continue
        if xpathsplit[posn]=="..":
            # ".." removes itself and its parent element
            del xpathsplit[posn]
            del xpathsplit[posn-1]
            posn-=1
            continue
            

        posn+=1
        pass

    if etxpath_isabs(xpath):
        resolved_xpath=canonical_etxpath_absjoin(*xpathsplit)
        pass
    else:
        resolved_xpath=canonical_etxpath_join(*xpathsplit)
        pass

    return resolved_xpath

def canonicalize_etxpath(fullxpath):
    """Canonicalize a composite xpath by
       1. Resolving all ".."'s and "."'s
       2. Canonicalizing filepath into an absolute canonical path
       3. Recombining filepath with xpath component

       In the future we might modify this to follow xpath symbolic links.
    """
    # print "initial fullxpath=%s" % (fullxpath)
    fullxpath=etxpath_resolve_dots(fullxpath)
    # print "fullxpath=%s" % (fullxpath)

    (filepath,xpath)=canonical_etxpath_break_out_file(fullxpath)
    # print "filepath=%s; xpath=%s" % (filepath,xpath)
    
    canonical_filepath=canonicalize_path(filepath)
    # print "canonical_filepath=%s" % (canonical_filepath)
    
    # print "new etxfilepath=%s" % (filepath_to_etxpath(canonical_filepath))
    
    full_canonical_xpath=filepath_to_etxpath(canonical_filepath)+xpath
    
    return full_canonical_xpath

def join_relative_etxpath(absolute_xpath,relative_xpath):
    # Suggest canonicalizing absolute_xpath first
    # Suggest re-canonicalizing after join. 
    return absolute_xpath+"/"+relative_xpath

def relative_etxpath_to(from_etxpath,to_etxpath):
    # From_etxpath and to_etxpath must be absolute
    assert(from_etxpath[0]=="/")
    from_etxpath=canonicalize_etxpath(from_etxpath)

    assert(to_etxpath[0]=="/")
    # print "to_etxpath_orig=%s" % (to_etxpath)
    to_etxpath=canonicalize_etxpath(to_etxpath)
    # print "to_etxpath_final=%s" % (to_etxpath)

    if from_etxpath.endswith("/"):
        from_etxpath=from_etxpath[:-1] # strip trailing slash if present from from
        pass
    
    from_etxpath_split=canonical_etxpath_split(from_etxpath)
    to_etxpath_split=canonical_etxpath_split(to_etxpath)

    # print "From_etxpath: %s" % (from_etxpath)
    # print "From_etxpath_split: %s" % (unicode(from_etxpath_split))

    # print "To_etxpath: %s" % (to_etxpath)
    # print "To_etxpath_split: %s" % (unicode(to_etxpath_split))

    # Determine common prefix
    pos=0
    while pos < len(from_etxpath_split) and pos < len(to_etxpath_split) and from_etxpath_split[pos]==to_etxpath_split[pos]:
        pos+=1
        pass

    relxpath_split=[]

    # print "Common prefix length = %d" % (pos)
    
    # convert path entries on 'from' side to '..'
    for entry in from_etxpath_split[pos:]:
        if len(entry) > 0: 
            relxpath_split.append('..')
            pass
        pass

    # add path entries on 'to' side
    for entry in to_etxpath_split[pos:]:
        if len(entry) > 0: 
            relxpath_split.append(entry)
            pass
        pass

    # print "relxpath_split=%s" % (unicode(relxpath_split))

    relxpath=canonical_etxpath_join(*relxpath_split)

    return relxpath
