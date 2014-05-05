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
