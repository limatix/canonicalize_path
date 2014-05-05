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

import canonicalize_path_module
import canonicalize_xpath_module

canonicalize_path=canonicalize_path_module.canonicalize_path


canonicalize_xpath=canonicalize_xpath_module.canonicalize_xpath
getelementxpath=canonicalize_xpath_module.getelementxpath
string_to_etxpath_expression=canonicalize_xpath_module.string_to_etxpath_expression
filepath_to_xpath=canonicalize_xpath_module.filepath_to_xpath
create_canonical_xpath=canonicalize_xpath_module.create_canonical_xpath
canonical_xpath_split=canonicalize_xpath_module.canonical_xpath_split
canonical_xpath_join=canonicalize_xpath_module.canonical_xpath_join
canonical_xpath_absjoin=canonicalize_xpath_module.canonical_xpath_absjoin
canonical_xpath_break_out_file=canonicalize_xpath_module.canonical_xpath_break_out_file
xpath_isabs=canonicalize_xpath_module.xpath_isabs
xpath_resolve_dots=canonicalize_xpath_module.xpath_resolve_dots
join_relative_xpath=canonicalize_xpath_module.join_relative_xpath
