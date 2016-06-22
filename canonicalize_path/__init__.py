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

A default (empty, but with examples) configuration is installed
in $PREFIX/etc/canonicalize_path/canonical_paths.conf.
You should put your site configuration in 
$PREFIX/etc/canonicalize_path/canonical_paths_local.conf


Suggested import:

try: 
   from canonicalize_path import canonicalize_path
   path
except ImportError:
   from os.path import realpath as canonicalize_path
   pass
"""

from . import canonicalize_path_module
from . import canonicalize_xpath_module
from . import canonical_url

canonicalize_relpath=canonicalize_path_module.canonicalize_relpath
canonicalize_filelist=canonicalize_path_module.canonicalize_filelist
rel_or_abs_path=canonicalize_path_module.rel_or_abs_path
pathsplit=canonicalize_path_module.pathsplit
canonicalize_path=canonicalize_path_module.canonicalize_path
relative_path_to=canonicalize_path_module.relative_path_to


canonicalize_etxpath=canonicalize_xpath_module.canonicalize_etxpath
getelementetxpath=canonicalize_xpath_module.getelementetxpath
string_to_etxpath_expression=canonicalize_xpath_module.string_to_etxpath_expression
etxpath2human=canonicalize_xpath_module.etxpath2human
getelementhumanxpath=canonicalize_xpath_module.getelementhumanxpath
filepath_to_etxpath=canonicalize_xpath_module.filepath_to_etxpath
create_canonical_etxpath=canonicalize_xpath_module.create_canonical_etxpath
canonical_etxpath_split=canonicalize_xpath_module.canonical_etxpath_split
canonical_etxpath_join=canonicalize_xpath_module.canonical_etxpath_join
canonical_etxpath_absjoin=canonicalize_xpath_module.canonical_etxpath_absjoin
canonical_etxpath_break_out_file=canonicalize_xpath_module.canonical_etxpath_break_out_file
etxpath_isabs=canonicalize_xpath_module.etxpath_isabs
etxpath_resolve_dots=canonicalize_xpath_module.etxpath_resolve_dots
join_relative_etxpath=canonicalize_xpath_module.join_relative_etxpath
relative_etxpath_to=canonicalize_xpath_module.relative_etxpath_to


etxpath2xpointer=canonical_url.etxpath2xpointer
href_fragment=canonical_url.href_fragment
href_context=canonical_url.href_context
