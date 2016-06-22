import sys

sys.path.insert(0,'../')

import canonicalize_path.canonical_url

etxpath="/{http://foo/bar}a/c/{http://bar/foo}b/{http://foo/bar}d/@{http://foo/foo}c"


xpointer=canonicalize_path.canonical_url.etxpath2xpointer(None,etxpath)

print(xpointer)
