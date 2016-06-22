
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

# References: XPointer XMLNS scheme, https://www.w3.org/TR/2002/PR-xptr-xmlns-20021113/
# XPOINTER framework
# https://www.w3.org/TR/2002/PR-xptr-framework-20021113/

# XPointer Registry
# https://www.w3.org/2005/04/xpointer-schemes/

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


# href_context is the underlying object wrapped by dc_value.hrefvalue
# Note that xmlrepr() and fromxml() methods do not track provenance,
# unlike dc_value.hrefvalue



import sys
import os
import collections
import re
import posixpath

from . import canonicalize_xpath_module
from .canonicalize_xpath_module import etxpath_isabs
from .canonicalize_xpath_module import canonical_etxpath_split
from .canonicalize_xpath_module import canonical_etxpath_absjoin
from .canonicalize_xpath_module import canonical_etxpath_join
from .canonicalize_xpath_module import getelementetxpath
from .canonicalize_xpath_module import string_to_etxpath_expression

from .canonicalize_path_module import relative_path_to
from .canonicalize_path_module import canonicalize_path

try:
    # py2.x
    from urllib import pathname2url
    from urllib import url2pathname
    from urllib import quote
    from urllib import unquote
    from urlparse import urlsplit
    from urlparse import urlunsplit
    from urlparse import urljoin
    from urlparse import urldefrag
    pass
except ImportError:
    # py3.x
    from urllib.request import pathname2url
    from urllib.request import url2pathname
    from urllib.parse import quote
    from urllib.parse import unquote
    from urllib.parse import urlsplit
    from urllib.parse import urlunsplit
    from urllib.parse import urljoin
    from urllib.parse import urldefrag
    pass



DCV="{http://thermal.cnde.iastate.edu/dcvalue}"


if hasattr(str,'maketrans'):
    caratparenescape_transtbl=str.maketrans({
        "^": "^^",
        "(": "^(",
        ")": "^)",
    })
    caratescape_transtbl=str.maketrans({
        "^": "^^",
    })
    
    pass


def parensbalanced(unescaped):
    # Check if parentheses are balanced and therefore we don't need
    # to escape them

    cnt=0
    for ch in unescaped:
        if ch=='(':
            cnt+=1
            pass
        elif cnt==')':
            cnt-=1
            if cnt < 0:
                return False
            pass
        pass
    return cnt==0



def caratescape(unescaped):
    # Perform the carat-based escaping of
    # parentheses and carats described in https://www.w3.org/TR/xptr-framework/

    if parensbalanced(unescaped):
        if hasattr(str,'maketrans'):
            # py >= 3.x
            return unescaped.translate(caratescape_transtbl)
            pass
        else:
            # py 2.6
            return re.sub('\^',lambda match: '^'+match.group(0),unescaped)
        pass
    else:
        # unbalanced parentheses... need to
        # escape parentheses as well as carat
        if hasattr(str,'maketrans'):
            # py >= 3.x
            return unescaped.translate(caratparenescape_transtbl)
            pass
        else:
            # py 2.6
            return re.sub('[()^]',lambda match: '^'+match.group(0),unescaped)
        pass
    pass


def etxpath2xpointer(context_etxpath,etxpath,desired_nsmap=None):
    # Gives canonical xpointer form if
    #   1. etxpath is absolute and canonicalized
    #   2. desired_nsmap is NOT given
    
    if not(etxpath_isabs(etxpath)):
        # relative path -- must join with context
        assert(context_etxpath is not None)

        if context_etxpath != "":
            etxpath=canonical_etxpath_join(context_etxpath,etxpath)
            pass
        pass

    if desired_nsmap is None:
        desired_nsmap={}
        pass
    
    desired_revnsmap=dict((v, k) for k, v in desired_nsmap.iteritems())
    
    # now need to break down etxpath and transform it into a 
    # simple xpath + a namespace mapping

    # This is quite similar to canonicalize_xpath_module.etxpath2human()
    
    etxpathcomponents=canonical_etxpath_split(etxpath)

    buildrevnsmap=collections.OrderedDict() # reverse nsmap: mapping to namespace to prefix
    used_prefixes=set([])
    buildpath=[]
    nextnsidx=0  # index of next "cn" namespace prefix to add 

    for pathentry in etxpathcomponents:

        if pathentry=="":
            # blank entry... i.e.leading entry of absolute path
            buildpath.append("")
            continue
        
        #print(pathentry)
        matchobj=canonicalize_xpath_module.xpath_clarkcvt_match_obj.match(pathentry)
        #print matchobj.groups()
        # group(1) is optional at sign group(2) is Clark prefix, group(3) is tag, group(4) is primary constraint, group(5) is secondary constraint
        optionalatsign=matchobj.group(1)
        clarkpfx=matchobj.group(2)
        
        if clarkpfx is not None:
            if clarkpfx[1:-1] not in buildrevnsmap:
                if clarkpfx[1:-1] in desired_revnsmap and desired_revnsmap[clarkpfx[1:-1]] not in used_prefixes:
                    useprefix=desired_revnsmap[clarkpfx[1:-1]]
                    pass
                else:
                    while "cn%d" % (nextnsidx) in used_prefixes:
                        nextnsidx+=1
                        pass
                    useprefix="cn%d" % (nextnsidx)
                    nextnsidx+=1
                    pass
                buildrevnsmap[clarkpfx[1:-1]]=useprefix
                used_prefixes.add(useprefix)                
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
        newtag=matchobj.group(3)

        primconstraint=matchobj.group(4)

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
        secconstraint=matchobj.group(5)  # brackets surrounding a number, 
                                         # e.g. [8]
        if secconstraint is None: 
            secconstraint=""
            pass
        
        buildpath.append(optionalatsign+newpfx+newtag+newprim+secconstraint)
        pass
    
    # join components
    joinpath=canonical_etxpath_join(*buildpath)
    
    # buildrevnsmap is an ordered dictionary so it is already sorted.
    nsmaplist=[ (nspre,url) for (url,nspre) in buildrevnsmap.items()]

    nsmapstrings=[ "xmlns(%s=%s)" % (nspre,caratescape(url)) for (nspre,url) in nsmaplist]

    xpointer="%sxpath1(%s)" % ("".join(nsmapstrings),caratescape(joinpath))
    return xpointer


def etxpath2xlink(context_etxpath,etxpath,desired_nsmap=None):
    #  ... This is obsolete because it uses etxpaths to cover the
    # file portion... and probably shouldn't be (isn't) used.
    
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
        (contextfile,contextetxpath)=canonicalize_xpath_module.canonical_etxpath_break_out_file(canonicalize_path(context_etxpath))
        targetpath=relative_path_to(os.path.split(contextfile)[0],targetfile)

        if targetpath==os.path.split(contextfile)[1]:
            # target file is the same file as contextfile
            targetpath=""  # will append hash+xpath
            pass
        pass
    else: 
        # absolute path -- targetpath = targefile
        targetpath=targetfile
        pass

    
    xlink="%s#%s" % (targetpath,etxpath2xpointer(None,targetetxpath,desired_nsmap=desired_nsmap))
    
    return xlink



parse_schemename=re.compile(r"""\s*\([^()^]+\)\s*""")

def parse_xpointer_schemename(frag):

    matchobj=parse_schemename.match(frag)

    if matchobj is None:
        raise ValueError("URL fragment %s does not start with a valid XPointer scheme name" % (frag))

    return (matchobj.end(),matchobj.group(1))

def parse_xpointer_schemeparams(frag):
    # Parse the scheme parameters. Also unescape '(', ')' and '^' as appropriate
    cnt=0

    if frag[0] != '(':
        raise ValueError("URL fragment scheme parameters %s do not start with '('" % (frag))
    
    params=""

    pos=0

    while pos < len(frag):
        ch=frag[pos]
        if ch=='(':
            cnt+=1
            params+=ch
            pass
        elif ch==')':
            cnt-=1
            params+=ch
            if cnt < 0:
                raise ValueError
            if cnt==0:
                return (cnt,params)
            pass
        elif ch=='^': # '^' is the escape character
            pos+=1
            params+=frag[pos]
            pass
        else:
            params+=ch
            pass
        pos+=1
        pass

    raise ValueError("URL fragment scheme parameters %s do not end with ')'" % (frag))

def parse_fragment_xpointer(frag):
    # returns # of characters, followed by list of (schemename, schemeparams) tuples
    
    frag_info=[]
    (numchars,schemename)=parse_xpointer_schemename(frag)
    (numchars2,schemeparams)=parse_xpointer_schemeparams(frag[numchars:])
    frag_info.append((schemename,schemeparams))
    
    if numchars+numchars2 < len(frag):
        (numchars3,nextfrags)=parse_fragment_xpointer(frag[(numchars+numchars2):])
        pass
    frag_info.extend(nextfrags)
    return (numchars+numchars2+numchars3,frag_info)



# Characters not allowed in namespace prefix:
# ' ' ! " ' # $ % & ( ) * + , : ; < = > ? @ ^ `~
parse_xmlns=re.compile(r"""\s*\(([^\s!"'#$%&()*+,:;<=>?@^`~]+)\s*=\s*([^\s)]+)\s*\)\s*""")

def parse_xpointer_xmlns(frag):
    matchobj=parse_xmlns.match(frag)
    if matchobj is None:
        raise ValueError("Error parsing XPointer xmlns declaration %s" % (frag))
    return (matchobj.group(1),matchobj.group(2))

# Only accepts reduced xpath from our canonical xpath generator
# /              Slash starting 
# (@?)           Optional at-sign
#([^\s!"'#$%&()*+,:;<=>?@^`~]+:)? optional namespace prefix
# ([^[\]/]+)      Tag name
# (?:([[] ... []])([[]\d+[]])?)?   Optional Constraint plus Optional Integer Constraint
# [^[\]"':]+?      Constraint content no quotes (non-greedy)
# "[^"]*"         Double Quoted string
# '[^']*'         Single quoted string
# (?:[^\s!"'#$%&()*+,:;<=>?@^`~]+:)  namespace prefix
# (?:(?:[^[\]"':]+?)|(?:"[^"]*")|(?:'[^']*')|(?:[^\s!"'#$%&()*+,:;<=>?@^`~]+:))+  Constraint content w/quotes
constrained_xpath_component_match_obj=re.compile(r"""/(@?)([^\s!"'#$%&()*+,:;<=>?@^`~]+:)?([^[\]/]+)(?:([[](?:(?:[^[\]"':]+?)|(?:"[^"]*")|(?:'[^']*')|(?:[^\s!"'#$%&()*+,:;<=>?@^`~]+:))+[]])([[]\d+[]])?)?"""  )

def constrained_xpath_split(xpath):
    """Split xpath into individual xpath components
    Only accepts ximple paths and reduced xpath from our canonical 
    xpath generator, not full general XPath queries"""

    #     
    
    text=""
    components=[]

    xpath=xpath.strip()
    
    absolute= xpath[0]=='/'

    if not absolute:
        xpath="/"+xpath  # put leading slash for parsing        
        pass
    else:
        components.append("")  # blank leading component represents absolute path
        pass
    
    for matchobj in constrained_xpath_component_match_obj.finditer(xpath):
        if matchobj is None: 
            raise SyntaxError("XPath parsing \"%s\" after \"%s\"." % (xpath,text))
        # group(1) is optional at-sign; group(2) is Namespace prefix, group(3) is tag, group(4) is primary constraint, group(5) is secondary constraint
        match=matchobj.group(0)
        text+=match
        components.append(match[1:]) # append to path component list, but drop '/'
        pass

    return components

#
#[^[\]"':]+? : Constraint content non-greedy
# "[^"]*"         Double Quoted string
# '[^']*'         Single quoted string
# [^\s!"'#$%&()*+,:;<=>?@^`~]+:  namespace prefix

constrainedxpath_primconstraint_match_re=re.compile(r"""([^[\]"':]+?)|("[^"]*")|('[^']*')|([^\s!"'#$%&()*+,:;<=>?@^`~]+:)""")

def constrained_xpath_split_to_etxpath(xpath,nsmap):
    """Split xpath into individual xpath components
    Only accepts ximple paths and reduced xpath from our canonical 
    xpath generator, not full general XPath queries"""

    #     
    
    text=""
    components=[]

    xpath=xpath.strip()
    
    absolute= xpath[0]=='/'

    if not absolute:
        xpath="/"+xpath  # put leading slash for parsing        
        pass
    else:
        components.append("")  # blank leading component represents absolute path
        pass
    
    for matchobj in constrained_xpath_component_match_obj.finditer(xpath):
        if matchobj is None: 
            raise SyntaxError("XPath parsing \"%s\" after \"%s\"." % (xpath,text))
        # group(1) is optional at-sign; group(2) is Namespace prefix, group(3) is tag, group(4) is primary constraint, group(5) is secondary constraint

        optionalatsign=matchobj.group(1)
        namespacepfx=matchobj.group(2)

        newnspfx=""
        if namespacepfx is not None:
            newnspfx="{"+nsmap[namespacepfx[:-1]]+"}"
            pass
        
        newtag=matchobj.group(3)

        primconstraint=matchobj.group(4)
        newprim=""


        if primconstraint is not None:
            newprim+="["
            # Iterate over elements of primconstraint
            for primconstraint_el_obj in constrainedxpath_primconstraint_match_re.finditer(primconstraint[1:-1]):
                # group(1) is arbitrary characters, group(2) is double-quoted strings, group(3) is single-quoted strings, group(4) is namespace prefix+":"
                if primconstraint_el_obj.group(4) is not None:
                    const_nspfx=primconstraint_el_obj.group(4)
                    if const_nspfx[:-1] in nsmap:
                        newprim+="{"+nsmap[const_nspfx[:-1]]+"}"
                        pass
                    else :
                        raise SyntaxError("No namespace mapping found for prefix %s" % (const_nspfx))
                        pass
                    pass
                else :
                    newprim+=primconstraint_el_obj.group(0) # attach everything
                    pass
                pass
            newprim+="]" # attach trailing close bracket
            pass

        secconstraint=matchobj.group(5)

        components.append(optionalatsign+newnspfx+newtag+newprim+secconstraint)

        
        pass

    return components




def parse_xpointer_constrained_xpath1(nsmap,frag):
    # returns ETXPath

    fragstrip=frag.strip()

    if fragstrip[0] != '(' or fragstrip[-1] != ')':
        return None

    xpath=frag[1:-1]

    # NOTE ***!!! Should uncomment try...except clause here
    # so that incompatible paths correctly fall back
    #try: 
    splitetxpath=constrained_xpath_split_to_etxpath(xpath,nsmap)
    #pass
    #except SyntaxError:
    #    return None
    
    # Leading "" on splitpath means absolute path
    #splitetxpath=[ xpathfrag2etxpathfrag(xpathfrag,nsmap) for xpathfrag in splitetxpath ]


    return "/".join(splitetxpath)


def parse_xpointer_constrained_etxpath1(frag):
    # returns ETXPath

    fragstrip=frag.strip()

    if fragstrip[0] != '(' or fragstrip[-1] != ')':
        return None

    etxpath=frag[1:-1]

    # NOTE ***!!! Should uncomment try...except clause here
    # so that incompatible paths correctly fall back
    #try: 
    splitetxpath=canonical_etxpath_split(etxpath)
    #    pass
    #except SyntaxError:
    #    return None
    
    # Leading "" on splitpath means absolute path
    #splitetxpath=[ xpathfrag2etxpathfrag(xpathfrag,nsmap) for xpathfrag in splitetxpath ]


    return "/".join(splitetxpath)



def nsmapstrings(nsmap_overrides):
    
    strlist=[ "xmlns(%s=%s)" % (nspre,caratescape(nsmap_overrides[nspre]))  for nspre in nsmap_overrides.keys() ] 
        
    
    return "".join(strlist)

class href_fragment(object):
    # Fragment is portion of URI after the '#'
    # We support fragments that identify a particular
    # element by id, and also fragments that identify
    # by XPointer with xmlns() and xpath() schemes

    type=None  # See TYPE_xxxx values below

    unquoted_string=None # for TYPE_UNANALYZED non-url-quoted string
    id=None # for TYPE_ID

    schemes_and_params=None # list of (nsmap, scheme, params) , for TYPE_XPOINTER_UNKNOWN. params are un-carat-escaped

    nsmap=None # desired namespace mapping for TYPE_CONSTRAINED_XPATH
    etxpath=None # ETXPath Clark Notation XPath for TYPE_CONSTRAINED_XPATH

    TYPE_UNANALYZED = 0 # We are lazy in doing analysis and haven't done it yet
    TYPE_ID = 1  # conventional fragment with no parentheses that references
                 # an element by ID
    TYPE_XPOINTER_UNKNOWN = 2 # Unknown XPointer structure. Assume it is
                              # dependent on xmlns() state 
    TYPE_CONSTRAINED_XPATH = 3 # Limited XPath structure used by canonical_xpath module. Permits better canonicalization 
    

    
    
    def __init__(self,fragment,etxpath=None,nsmap=None):
        # fragment should not be URL-quoted
        self.unquoted_string=fragment
        self.type=self.TYPE_UNANALYZED

        if etxpath is not None:
            # Don't use this directly... use from_constrained_etxpath()
            self.type=self.TYPE_CONSTRAINED_XPATH
            self.etxpath=etxpath
            self.nsmap=nsmap
            if self.nsmap is None:
                self.nsmap={}
                pass
            
            pass
        pass

    @classmethod
    def from_constrained_etxpath(cls,etxpath,nsmap=None):
        return href_fragment(None,etxpath=etxpath,nsmap=nsmap)
    
    def analyze(self):

        if self.type!=self.TYPE_UNANALYZED:
            return

        fragment=self.unquoted_string
        if '(' in fragment:
            # interpret as xpointer

            self.type=self.TYPE_XPOINTER_UNKNOWN # Will override to TYPE_CONSTRAINED_XPATH if we pass all of the tests
            
            (numchars,frag_info) = parse_fragment_xpointer(fragment)

            # nsmap_frag_info = [ (collections.OrderedDict(nsmap_context),schemename,schemeparams) for (schemename,schemeparams) in frag_info ]


            nsmap_overrides=collections.OrderedDict()

            self.schemes_and_params=[] # list of (nsmap, scheme, params) , for TYPE_XPOINTER_UNKNOWN
            for (schemename, schemeparams) in frag_info:
                if schemename=="xmlns":
                    (nspre,nsval)=parse_xpointer_xmlns(schemeparams)
                    if nspre in nsmap_overrides:
                        del nsmap_overrides[nspre]
                        pass
                    
                    nsmap_overrides[nspre]=nsval
                    pass
                else:
                    self.schemes_and_params.append(nsmap_overrides,schemename,schemeparams)
                    pass
                pass
            
            # Check if we satisfy requirements of TYPE_CONSTRAINED_XPATH, The limited XPath structure used by canonical_xpath module
            
            # Requirements: No fall-through, absolute xpath1 scheme, full nsmap specified or etxpath1 
            if len(self.schemes_and_params)==1:
                (nsmap_overrides,schemename,schemeparams)=self.schemes_and_params[0]
                if schemename=="xpath1":
                    etxpath=parse_xpointer_constrained_xpath1(nsmap_overrides,schemeparams)

                    if etxpath != None and etxpath[0]=='/':
                        self.type=self.TYPE_CONSTRAINED_XPATH
                        self.nsmap=nsmap_overrides
                        self.etxpath=etxpath
                        pass
                    pass
                elif schemename=="etxpath1":
                    etxpath=parse_xpointer_constrained_etxpath1(schemeparams)

                    if etxpath != None and etxpath[0]=='/':
                        self.type=self.TYPE_CONSTRAINED_XPATH
                        self.nsmap=nsmap_overrides
                        self.etxpath=etxpath
                        pass
                    pass
                pass
            
            pass
        else:
            self.type=self.TYPE_ID
            self.id=fragment
            pass
        
            
        pass

    def assemble(self):
        # Re-assemble fragment according to type
        if self.type==self.TYPE_ID:
            self.unquoted_string=self.id
            pass
        elif self.type==self.TYPE_XPOINTER_UNKNOWN:
            self.unquoted_string="".join([ nsmapstrings(nsmap_overrides)+schemename+caratescape(schemeparams) for (nsmap_overrides,schemename,schemeparams) in self.schemes_and_params ])
            pass
        elif self.type==self.TYPE_CONSTRAINED_XPATH:
            self.unquoted_string=etxpath2xpointer(None,self.etxpath,desired_nsmap=self.nsmap)
            
            pass
        elif self.type==self.TYPE_UNANALYZED:
            # nothing to do
            pass
        else:
            assert(0)
            pass
        pass
    
    
    def get_fragment(self):
        if self.unquoted_string is None:
            self.assemble()
            pass
        
        # return non-url-quoted string
        return self.unquoted_string


    def get_canonical(self):
        self.analyze()

        if self.type==self.TYPE_CONSTRAINED_XPATH:
            return "etxpath1(%s)" % (caratescape(self.etxpath))  # etxpath1 is not standard!!! We just use this for our canonicalization
        else:
            if self.unquoted_string is None:
                self.assemble()
                pass
            return self.unquoted_string
        pass

    def evaluate(self,xmldocu,refelement,noprovenance=False):
        self.analyze()

        if self.type==self.TYPE_ID:
            idstr=string_to_etxpath_expression(self.id)
            return xmldocu.xpath("//*[id=%s or xml:id=%s]" % (idstr,idstr),noprovenance=noprovenance)
        elif self.type==self.TYPE_XPOINTER_UNKNOWN:
            if all([ scheme=="xpath1" for (nsmap,scheme,params) in self.schemes_and_params ]):
                # XPath1 xpointer... we can do this!

                # Follow fall-through process of XPointer framework
                result_set=[]
                pos=0
                while len(result_set)==0:
                    (nsmap,scheme,params)=self.schemes_and_params[pos]
                    if params[0] != '(' or params[-1] != ')':
                        raise ValueError("Error parsing xpath1 path %s" % (params))
                    xpath=params[1:-1]

                    result_set=xmldocu.xpath(xpath,namespaces=nsmap,contextnode=refelement,noprovenance=noprovenance)
                    
                    pos+=1
                    pass
                return result_set
            raise ValueError("Unknown XPointer scheme in fragment %s" % (self.unquoted_string))
        
        elif type==self.TYPE_CONSTRAINED_XPATH:
            result_set=xmldocu.etxpath(self.etxpath,contextnode=refelement,noprovenance=noprovenance)
            return result_set
        else:
            assert(0) # unknown type!!!
        pass
    pass

class href_context(object):
    # hypertext reference with context

    # an href is a URL reference with
    # a context. 

    # Everything has to have a context, unless the
    # supplied URL is guaranteed to be absolute and
    # defines a URL scheme. If you just
    # have a file path, then that context is the
    # current directory '.'
    #
    # The HREF is represented as a list of URL contexts
    # that when joined represent the desired URL.
    # If there is no leading context that defines a URL scheme,
    # then the scheme is assumed to be file://. If there is no
    # leading context that defines an absolute URL path, then that
    # path is presumed to be relative to the current directory.

    # Note that contexts may include a file part, WHICH IS STRIPPED.
    # A context intended to be a directory should include the
    # trailing slash.

    # Note that URL's and contexts can be generated from
    # filesystem paths with urllib.[request.]pathname2url()

    # Note that this is 'final' and should not be changed once
    # created
    
    contextlist=None  # list (actually tuple, once finalized) of URL's (QUOTED)

    fragment=None # Fragment is portion of URI after the '#'
                  # We support fragments that identify a particular
                  # element by id, and also fragments that identify
                  # by XPointer with xmlns() and xpath() schemes
                  # This is a class href_fragment that
                  # represents the UNQUOTED fragment

    # caches of commonly evaluated params
    absurl_cache=None
    canonicalize_cache=None
    hash_cache=None
    
    def __init__(self,URL,contexthref=None,fragment=None):
        contextlist=[]
        gotURL=False
        

        #import pdb as pythondb
        #pythondb.set_trace()

        if URL is None and contexthref is None:
            self.contextlist=None
            # blank
            return

        if contexthref is not None and not hasattr(contexthref,"contextlist"):

            # if a tuple, interpret as a contextlist  otherwise contexthref presumed to be a string...
            assert(isinstance(contexthref,basestring) or isinstance(contexthref,tuple))
            contexthref=href_context(contexthref)
            pass
        
        # include context, if present
        if contexthref is not None and contexthref.contextlist is not None:            
            contextlist.extend(contexthref.contextlist)
            pass
        
        if hasattr(URL,"contextlist"):
            # URL is actually an href_context
            if URL.contextlist is not None:
                contextlist.extend(URL.contextlist)
                if len(URL.contextlist) > 0:
                    gotURL=True
                    pass
                pass
            pass
        elif isinstance(URL,tuple):
            # Treat tuple as contextlist
            contextlist.extend(URL)
            #if len(URL) > 0:
            gotURL=True
            #    pass
        else:
            # URL presumed to be a string
            assert(isinstance(URL,basestring))
            if URL != "":
                contextlist.append(URL)
                gotURL=True
                pass
            else:
                self.contextlist=None
                return
            pass

        if not gotURL:
            # if no URL provided at all (just blank) then context means nothing.
            # Just return completely blank
            self.contextlist=None
            return
        
        # go through context list from end to start
        # and cull out unnecessary leading context
        culledcontext=[]
        foundabspath=False
        for pos in range(len(contextlist)-1,-1,-1):
            thiscontext=contextlist[pos]
            parsed=urlsplit(thiscontext)

            if parsed.fragment != "":
                if pos==len(contextlist)-1: # only latest entry generally has meaning
                    # rebuild context without fragment
                    (thiscontext,fragment)=urldefrag(thiscontext)
                    self.fragment=href_fragment(unquote(fragment))
                    
                    pass
                pass
            
            if foundabspath and parsed.scheme=='':
                # already have an absolute path, and no scheme specified...
                # another absolute or relative path with no scheme is useless
                continue
            if parsed.path.startswith('/'):
                foundabspath=True
                pass
            # add on to culled context
            culledcontext.insert(0,thiscontext)
            
            if len(parsed.scheme) > 0:
                # got a scheme... nothing else matters
                break
            pass
        self.contextlist=tuple(culledcontext)
        pass

    def isblank(self):
        return self.contextlist is None

    def ismem(self):
        if self.contextlist is None or len(self.contextlist)==0:
            return False
        # since unnecessary context is culled on creation, the
        # scheme comes from the scheme of the first element
        return urlsplit(self.contextlist[0]).scheme=='mem'

    def ishttp(self):
        if self.contextlist is None or len(self.contextlist)==0:
            return False
        # since unnecessary context is culled on creation, the
        # scheme comes from the scheme of the first element
        return urlsplit(self.contextlist[0]).scheme=='http'

    def isfile(self):
        if self.contextlist is None:
            return False
        if len(self.contextlist)==0:
            return True

        # since unnecessary context is culled on creation, the
        # scheme comes from the scheme of the first element
        scheme=urlsplit(self.contextlist[0]).scheme

        return scheme=="" or scheme=="file"

    def __str__(self):
        if self.contextlist is None:
            return ""
        return self.absurl()

    
    def absurl(self) :
        if self.absurl_cache is not None:
            return self.absurl_cache
        
        
        # returns full escaped URL with complete context
        if len(self.contextlist)==0:
            return "."
        if self.contextlist is None:
            return ""
        

        URL=""
        if self.fragment is not None:
            URL=quote("#"+self.fragment.get_fragment())
            pass
        
        for pos in range(len(self.contextlist)-1,-1,-1):
            URL=urljoin(self.contextlist[pos],URL)
            pass
        
        self.absurl_cache=URL
        return URL


    # Stored as path, not as URL    
    def islocalfile(self):
        return self.isfile()



    def attempt_relative_url(self,new_context):
        # return a relative url string (if possible) which,
        # if it is indeed relative, will be relative to the
        # new context

        # convert new_context to an href, if it is not
        if not hasattr(new_context,"contextlist"):
            new_context=href_context(new_context)
            pass

        # search for common ancestors of our context.
        # if we have common ancestors, we can define a
        # relative URL
        common_context=0
        for cnt in range(min(len(new_context.contextlist),len(self.contextlist))):
            if new_context.contextlist[cnt]==self.contextlist[cnt]:
                common_context+=1
                pass
            else:
                break
            pass
        # Join up remaining new_context
        new_context_URL=""
        for pos in range(len(new_context.contextlist)-1,common_context-1,-1):
            new_context_URL=urljoin(new_context.contextlist[pos],new_context_URL)
            pass

        # join up remaining pieces of our url
        our_URL=""
        our_fragment=""
        if self.fragment is not None:
            our_fragment=quote("#"+self.fragment.get_fragment())
            pass

            
        for pos in range(len(self.contextlist)-1,common_context-1,-1):
            our_URL=urljoin(self.contextlist[pos],our_URL)
            pass

        new_context_parsed=urlsplit(new_context_URL)
        our_parsed=urlsplit(urljoin(our_URL,our_fragment))
        if new_context_parsed.scheme != "" or our_parsed.scheme != "":
            # Removing common context ancestors did not remove
            # all scheme specification....
            # relative URL of any type not possible...
            # generate absolute URL with scheme
            return self.absurl()

        if new_context_parsed.path.startswith("/") or our_parsed.path.startswith("/"):
            # Removing common context ancestors did not eliminate absolute paths

            if our_parsed.path.startswith("/"):
                # absolute path within the context... Return it directly
                return urlunsplit(("","",our_parsed.path,our_parsed.query,our_parsed.fragment))
                # return our_parsed.path

            # Remaining case is that unique context of our URL is not absolute
            # but unique context of desired context IS absolute

            # For example
            # ours:
            #  http://localhost/foo/  bar.html
            # desired:
            #  http://localhost/foo/ /fubar/bar/
            #
            # No straightforward way to do this... just drop down to absolute
            return self.absurl()

        # now we have two paths:  new_context_URL and our_URL, both of which
        # are relative...
        # i.e new_context_URL='foo/bar/fubar.html'
        #  and  our_url='fubar/foo/bar.html'
        # The result of this would be ../../fubar/foo/bar.html

        # or new_context_URL='../foo/bar/../fubar.html' 
        #  and  our_url='fubar/foo/bar.html'
        # The result of this one would be: Can't do it
        #  ... leading '..' on new context is a directory we don't
        #      know the name of

        # or new_context_URL='foo/bar/../fubar.html' 
        #  and  our_url='../fubar/../foo/bar.html'
        # result is ../../foo/bar.html
        #  
        # note that the file part of context URLs is to be ignored
        # We use the posixpath module to manipulate these paths
        # (see http://stackoverflow.com/questions/7894384/python-get-url-path-sections)
        new_context_path=posixpath.split(new_context_URL)[0]

        
        # new context path now refers to a directory without trailing '/'
        # now do path normalization
        normalized_context_path=posixpath.normpath(new_context_path)  # directory without trailing slash
        if normalized_context_path.startswith("../"):
            # leading '..' on context is directory we don't and can't know the name
            # of...

            if common_context >= 1:
                # Join with last bit of common context and retry

                joined_self=href_context(urljoin(self.contextlist[common_context-1],urljoin(our_URL,our_fragment)),contexthref=self.contextlist[:(common_context-1)])

                joined_new_context=href_context(urljoin(new_context.contextlist[common_context-1],new_context_URL),contexthref=new_context.contextlist[:(common_context-1)])

                return joined_self.attempt_relative_url(joined_new_context)
            else:
                sys.stderr.write("href_in_context.href_context.attempt_relative_url(): Trying to form a relative URL from %s with leading '..' on context %s... this is not possible. Dropping down to absolute URL\n" % (self.absurl(),new_context.absurl()))
                
                # Bail and drop down to absolute path
                return self.absurl()
            pass
        


        # turn normalize_context_path entries into leading '..' entries in resultpath 
        resultpath=""
        (dirpart,filepart)=posixpath.split(normalized_context_path)

        while len(dirpart) > 0:
            assert(filepart != '..') # can't deal with pulling off a '..'
            if filepart != '.':
                resultpath=posixpath.join(resultpath,'..')
                pass
            
            (dirpart,filepart)=posixpath.split(dirpart)
            pass

        # Above loop doesn't count filepart
        if len(filepart) > 0 and filepart != ".":
            resultpath=posixpath.join(resultpath,'..')
            pass


        # append our_URL to resultpath
        resultpath=posixpath.join(resultpath,our_URL)

        # Eliminate unnecessary '..'s' in resultpath
        normalized_result_path=posixpath.normpath(resultpath)
        # posixpath.normpath removes trailing slash, but we want to keep that...
        if our_URL.endswith("/") and not(normalized_result_path.endswith("/")):
            normalized_result_path += "/"
            pass

        # Eliminate unnecessary '..'s' in resultpath based on
        # context

        #***!!!FIXME... this handles a resulting
        # url of ../foo/bar.xml on a context of foo/
        # but not multiple layers, e.g. resulting url
        # of ../../fubar/foo/bar.xml on a context of fubar/foo/
        if normalized_result_path.startswith("../"):
            remaining_result_path=normalized_result_path[3:]
            context_path_fragment=posixpath.split(normalized_context_path)[1]+"/"

            if remaining_result_path.startswith("../"):
                sys.stderr.write("href_in_context.href_context.attempt_relative_url: FIXME: Need better algorithm for matching leading ..'s on URL result path with context path fragments\n")
            # Does the remaining path after the "../" match the last fragment of our context path?
            if not remaining_result_path.startswith("../") and remaining_result_path.startswith(context_path_fragment):
                # If so, remove both
                normalized_result_path=remaining_result_path[len(context_path_fragment):]
                pass
            
            pass
        
        return urljoin(normalized_result_path,our_fragment)
    

    def attempt_relative_href(self,new_context):
        relative_url=self.attempt_relative_url(new_context)

        return href_context(relative_url,contexthref=new_context)

    
    def xmlrepr(self,xmldocu,element,force_abs_href=False):

        #import pdb as pythondb
        #if element.tag=="{http://thermal.cnde.iastate.edu/datacollect}dgsfile":
        #    pythondb.set_trace()

        #if xml_attribute is None:
        xml_attribute="xlink:href"
            
        #assert(xml_attribute=="xlink:href")
        #assert(not is_file_in_dest) # This derived class uses its internal context specification, not the is_file_in_dest parameter
        # NOTE: if xml_attribute is provided, xmldocu must be also.

        #print "xmlrepr!" + self.str
        # clear out any old attributes in the dcvalue namespace
        oldattrs=element.attrib.keys()
        for oldattr in oldattrs:
            if oldattr.startswith(DCV):
                del element.attrib[oldattr]
                pass
            pass

        if self.isblank():
            # Blank entry: clear out the xlink:href attribute
            if xml_attribute in element.attrib:
                xmldocu.remattr(element,xml_attribute)
                pass
            xmldocu.modified=True
            return

        contexthref=xmldocu.getcontexthref()

        if (not force_abs_href) and (contexthref is not None) and (not contexthref.isblank()) and (not self.isblank()):
            url=self.attempt_relative_url(xmldocu.getcontexthref())
            pass
        else:
            url=self.absurl()  # Create our best-of-ability absolute url
            pass
        xmldocu.setattr(element,xml_attribute,url)
        xmldocu.modified=True

        pass

    def get_bare_quoted_filename(self):
        if self.contextlist is None or len(self.contextlist) < 1:
            return ""
        
        parsed=urlsplit(self.contextlist[-1])
        return posixpath.split(parsed.path)[1]

    def get_bare_unquoted_filename(self):
        quoted_filename=self.get_bare_quoted_filename()
        return unquote(quoted_filename)

    
    def getpath(self):
        assert(self.isfile())
        
        parsed=urlsplit(self.absurl())

        if parsed.query != "":
            raise ValueError("Query string not meaningful for file URL")
        
        
        path=url2pathname(parsed.path)
        return path

    def has_fragment(self):
        return self.fragment is None
    
    def getunquotedfragment(self):
        if self.fragment is None:
            return ""
        return '#'+self.fragment.get_fragment()

    def getquotedfragment(self):
        if self.fragment is None:
            return ""
        return quote("#"+self.fragment.get_fragment())

    def leafless(self):
        # hrefvalues can include path and file. When defining a context, you
        # often want to remove the file part. This routine copies a href and
        # removes the file part, (but leaves the trailing slash)

        if len(self.contextlist) < 1:
            return self
        
        parsed=urlsplit(self.contextlist[-1])
        leaflesspath=posixpath.split(parsed.path)[0]
        if len(leaflesspath) > 0 and not leaflesspath.endswith("/"):
            leaflesspath+="/"
            pass

        if len(leaflesspath) > 0:
            leaflessurl=urlunsplit((parsed[0],parsed[1],leaflesspath,parsed[3],parsed[4]))
            pass

        # Start with all but last element of href context
        newcontextlist=[]
        newcontextlist.extend(self.contextlist[:-1])
        if len(leaflesspath) > 0:
            newcontextlist.append(leaflessurl)
            pass
        
        return href_context(tuple(newcontextlist))


    @classmethod
    def fromxml(cls,xmldocu,element):
        # NOTE: to use xml_attribute you must provide xmldocu)
        
        if xmldocu is not None:
            xmlcontexthref=xmldocu.getcontexthref()
            pass
        else:
            xmlcontexthref=None
            pass

        #if xml_attribute is None:
        xml_attribute="xlink:href"

        # assert(xml_attribute=="xlink:href")

        #assert(not is_file_in_dest) # This derived class uses its internal context specification, not the is_file_in_dest parameter

        text=xmldocu.getattr(element,xml_attribute,"")

        val=href_context(text,contexthref=xmlcontexthref)

        return val

    def __hash__(self):
        if self.hash_cache is not None:
            return self.hash_cache
        
        self.hash_cache=self.canonicalize().__hash__()
        return self.hash_cache

    def __eq__(self,other) :
        if other is None:
            return False
        
        if self.contextlist is None and other.contextlist is None:
            return True

        if (self.contextlist is None) ^ (other.contextlist is None):  # ^ is XOR operator
            return False


        return self.absurl()==other.absurl()


    def canonicalize(self):
        # return canonicalized form
        # Note that we are not currently able to __interpret__ this
        # canonicalized form, but it's still good for hashing
        # and comparison

        if self.canonicalize_cache is not None:
            return self.canonicalize_cache
        
        if len(self.contextlist)==0:
            return "."
        if self.contextlist is None:
            return ""

        URL=""
        if self.fragment is not None:
            URL=quote("#"+self.fragment.get_canonical())
            pass


        if self.isfile():
            path=self.getpath()
            canonpath=canonicalize_path(path)
            URL=urljoin(pathname2url(canonpath),URL)
            pass
        else:
            for pos in range(len(self.contextlist)-1,-1,-1):
                URL=urljoin(self.contextlist[pos],URL)
                pass
            pass
        self.canonicalize_cache=URL
        return URL

    @classmethod
    def fromelement(cls,xmldocu,element,tag_index_paths_override=None):
        # Get a HREF pointing at the specified element of xmldocu,
        # using XPointer to probe into the document
        # xmldocu must be at least read-only locked
        
        filehref=xmldocu.get_filehref().value()
        etxpath=getelementetxpath(xmldocu.doc,element,tag_index_paths_override=tag_index_paths_override)

        href=href_context(filehref,fragment=href_fragment.from_constrained_etxpath(etxpath,element.nsmap))

        return href
    
    
    pass