import sys
import os.path
import string
import re

from pkg_resources import resource_string

from canonicalize_path_module import canonicalize_path
from canonicalize_path_module import pathsplit



try: 
    from lxml import etree
    pass
except ImportError: 
    pass
    
__install_prefix__=resource_string(__name__, 'install_prefix.txt')

if __install_prefix__=="/usr": 
    config_dir='/etc/canonicalize_path'
    pass
else:
    config_dir=os.path.join(__install_prefix__,"etc","canonicalize_path")
    pass

DBDIR="{http://thermal.cnde.iastate.edu/databrowse/dir}dir"
DBFILE="{http://thermal.cnde.iastate.edu/databrowse/dir}file"


# Example tag_index_paths.conf:
# {
#   "{http://thermal.cnde.iastate.edu/databrowse/dir}dir":  "@name",
#   "{http://thermal.cnde.iastate.edu/databrowse/dir}file": "@basename",
#   "{http://thermal.cnde.iastate.edu/datacollect}measurement": "measnum",
#
# }

tag_index_paths_conf=file(os.path.join(config_dir,"tag_index_paths.conf"))
exec(u'tag_index_paths='+tag_index_paths_conf.read().decode('utf-8'))
tag_index_paths_conf.close()

try: 
    tag_index_paths_local_conf=file(os.path.join(config_dir,"tag_index_paths_local.conf"))
    exec(u'tag_index_paths.update('+tag_index_paths_local.read().decode('utf-8')+')')
    tag_index_paths_local.close()
    pass
except IOError:
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
        elif isinstance(strval,collections.Sequence) and len(strval)==1:
            strval=strval[0].text
            pass 
        else: 
            raise ValueError("Invalid parameter value (%s) for converting tag %s into an XPath matching expression: Must be a node, length-one node-set, or string. See also tag_index_paths.conf and tag_index_paths_local.conf" % (str(node),element.tag))
        pass
        
    
    if strval.find("\"") < 0:
        return "\""+strval+"\"" # use double quotes
    
    if strval.find("\'") < 0:
        return "\'"+strval+"\'" # use single quotes
    
    # use Concat with double quotes so single quotes are OK

    splitstr=strval.split("\"") # split into segments that don't have double quotes
    
    quotedsplitstr=["\""+component+"\"" for component in splitstr] # Put quotes around each segment
    return "concat(%s)" % (string.join(quotedsplitstr,",'\"',")) # Join with double quotes and return in a concat expression

    


def getelementxpath(doc,element):
    # returns full Clark notation xpath (see ETXPath)
    # with leading slash and root element defined 
    parent=element.getparent()
    if parent is None:
        # at root 
        assert(doc.getroot() is element)
        pathel="/%s" % (element.tag)
        return pathel
    else :
        # recursive call to get earlier path components
        pathprefix=getelementxpath(doc,parent)

        if element.tag in tag_index_paths:
            indices=tag_index_paths[element.tag]  # get index xpath expression for identifying this element
            
            if isinstance(indices,basestring):
                # if only one index location is provided...
                indices=(indices,)
                pass
            
            indexstr=""

            for index in indices: 
                # now extract the value of this expression for our element
                ETXindexval=etree.ETXPath(index) # if etree is None here you need to install python-lxml
                indexval=ETXindexval(element) # perform xpath lookup
                if not isinstance(indexval,basestring):
                    # Did we get a node?
                    if hasattr(strval,"tag"):
                        indexval=indexval.text
                        pass
                    # Did we get a length-1 node-set?
                    elif isinstance(indexval,collections.Sequence) and len(indexval)==1:
                        indexval=indexval[0].text
                        pass 
                    elif isinstance(indexval,collections.Sequence) and len(indexval) > 1:
                        raise ValueError("Got multiple nodes searching for index element %s in " % (index))
                        pass
                if len(indexval) > 0:  # if we found a suitable non-empty string
                    indexvalexpr=string_to_etxpath_expression(indexval)  
                    indexstr="[%s=%s]" % (index,indexvalexpr)
                    # No need to go on. We found a suitable index
                    break
                pass
            pass
        else :
            indexstr=""
            pass
        ETXindex=etree.ETXPath("%s%s" % (element.tag,indexstr))  # if etree is None here you need to install python-lxml
    
        # Try this index on parent
        siblings=ETXindex(parent)
        elnum=[ i for i in range(len(siblings)) if siblings[i] is element ][0]+1

        pathel="%s%s[%d]" (element.tag,indexstr,elnum)
    
        return "%s/%s" % (pathprefix,pathel)
    pass
 

def filepath_to_xpath(filepath):
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
    pathcomponents=["%s[name=%s]" % (DBDIR,string_to_etxpath_expression(fc)) for fc in dircomponents if fc != ""]
    
    if filecomponent is not None:
        pathcomponents.append("%s[basename=%s]" % (DBFILE,string_to_etxpath_expression(filecomponent)))
        pass
        
    if os.path.isabs():
        pathcomponents.insert(0,'') # force leading slash after join
        pass

    filexpath=string.join(pathcomponents,'/')
    
    return filexpath

def create_canonical_xpath(filepath,doc,element):
    """Find a canonical absolute (Clark notation) xpath representation based 
       off the filesystem root for the specified element within
       doc. 

       filepath should be a relative or absolute path to doc.
       doc is the etree.ElementTree document containing element
       element is an XML etree.Element within doc
    """

    canonical_filepath=canonicalize_path(filepath)

    if doc is not None:
        xpath=getelementxpath(doc,element)
        pass
    else :
        xpath=""
        pass

    filexpath=filepath_to_xpath(canonical_filepath)

    fullxpath=filexpath+xpath
    
    return fullxpath

# Only accepts reduced xpath from our canonical xpath generator

# /({[^}]+})?     Optional Clark notation
# ([^[\]/]+)      Tag name
# (?:([[] ... []])([[]\d+[]])?)?   Optional Constraint plus Optional Integer Constraint
# [^[\]/"']+      Constraint content no quotes
# "[^"]*"         Double Quoted string
# '[^']*'         Single quoted string
# (?:(?:[^[\]/"']+)|(?:"[^"]*")|(?:'[^']*'))+  Constraint content w/quotes
xpath_component_match_re=r"""({[^}]+})?([^[\]/]+)(?:([[](?:(?:[^[\]/"']+)|(?:"[^"]*")|(?:'[^']*'))+[]])([[]\d+[]])?)?"""
xpath_component_match_obj=re.compile(xpath_component_match_re)

def canonical_xpath_split(fullxpath):
    """Split xpath into individual xpath components
    Only accepts ximple paths and reduced xpath from our canonical 
    xpath generator, not full general XPath queries"""

    #     
    
    text=""
    components=[]
    for matchobj in re.finditer("/"+xpath_component_match_re,fullxpath):
        # for matchobj in re.finditer(r"""/({[^}]+})?([^[\]/]+)([[](?:(?:[^[\]/"']+)|(?:"[^"]*")|(?:'[^']*'))+[]])([[]\d+[]])?""",fullxpath):
        if matchobj is None: 
            raise SyntaxError("XPath parsing \"%s\" after \"%s\"." % (fullxpath,text))
        # group(1) is Clark prefix, group(2) is tag, group(3) is primary constraint, group(4) is secondary constraint
        match=matchobj.group(0)
        text+=match
        components.append(match[1:]) # append to path component list, but drop '/'
        pass

    return components

def canonical_xpath_join(*components):
    # Does NOT supply additional leading "/" to make the path absolute
    return string.join(components,"/")    

def canonical_xpath_absjoin(*components):
    # DOES  supply leading "/" to make the path absolute
    components.insert("",0)
    return string.join(components,"/")
    
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
constraint_match_re=r"""\[name=(?:(?:concat\(((?:(?:[^)"']*)|(?:"[^"]*")|(?:'[^']*'))+)\))|(?:"([^"]*)")|(?:'([^']*)'))\]$"""
constraint_match_obj=re.compile(constraint_match_re)

constraint_filematch_re=r"""\[basename=(?:(?:concat\(((?:(?:[^)"']*)|(?:"[^"]*")|(?:'[^']*'))+)\))|(?:"([^"]*)")|(?:'([^']*)'))\]$"""
constraint_filematch_obj=re.compile(constraint_filematch_re)



# (?:"([^"]*)")     Double quoted string
concat_match_re = r"""(?:"([^"]*)"),?"""


def canonical_xpath_break_out_file(fullxpath):
    """Break out file path from xpath components of a canonical xpath
    Presumes the file portion covers the entire leading 
    sequence of dbdir:dir an dbdir:file elements
    returns (filepath, xpath within that file)"""
    
    components=canonical_xpath_split(fullxpath)
    
    isdir=True

    if os.path.sep=="/":
        filepath="/"
        pass
    else:
        filepath=""
        pass
    
    xpath=""

    compnum=0
    while isdir:
        component=components[compnum]
        matchobj=xpath_component_match_obj.match(component)
        (clarkpfx,tag,primconstraint,secconstraint)=matchobj.groups()
        # print matchobj.groups()
        
        if (clarkpfx=="{http://thermal.cnde.iastate.edu/databrowse/dir}" and
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
                    filepath=os.path.join(filepath,string.join([matchobj.group(1) for matchobj in re.finditer(concat_match_re,concatconstraint)],""))
                    pass
                compnum+=1
                continue
            pass
            isdir=False
        pass
    
    if len(components) > compnum:
        xpath = "/"+ string.join(components[compnum:],"/")
        pass

    return (filepath,xpath)

def xpath_isabs(xpath):
    """Returns TRUE if the xpath is absolute (leading /)"""
    return xpath[0]=='/'
    

def xpath_resolve_dots(xpath):
    
    xpathsplit=canonical_xpath_split(xpath)

    posn=0
    while posn < len(xpathsplit):
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

    if xpath_isabs(xpath):
        resolved_xpath=canonical_xpath_absjoin(xpathsplit)
        pass
    else:
        resolved_xpath=canonical_xpath_join(xpathsplit)
        pass

    return resolved_xpath

def canonicalize_xpath(fullxpath):
    """Canonicalize a composite xpath by
       1. Resolving all ".."'s and "."'s
       2. Canonicalizing filepath into an absolute canonical path
       3. Recombining filepath with xpath component

       In the future we might modify this to follow xpath symbolic links.
    """
    fullxpath=xpath_resolve_dots(fullxpath)

    (filepath,xpath)=canonical_xpath_break_out_file(fullxpath)

    canonical_filepath=canonicalize_path(filepath)
    
    full_canonical_xpath=filepath_to_xpath(canonical_filepath)+xpath
    
    return full_canonical_xpath

def join_relative_xpath(absolute_xpath,relative_xpath):
    # Suggest canonicalizing absolute_xpath first
    # Suggest re-canonicalizing after join. 
    return absolute_xpath+"/"+relative_xpath
