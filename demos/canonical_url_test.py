import sys

sys.path.insert(0,'../')

import canonicalize_path.canonical_url
from canonicalize_path.canonical_url import href_context

# some unit tests on href_context

assert(href_context(('/tmp/','foo/')).attempt_relative_url(href_context(('/tmp/','foo/','bar.html')))=='.')
assert(href_context(('/tmp/','foo/','bar.html')).attempt_relative_url(href_context(('/tmp/','foo/','bar.html')))=='')
assert(href_context(('/tmp/','foo/','bar.html#fragment')).attempt_relative_url(href_context(('/tmp/','foo/','bar.html')))=='#fragment')
assert(href_context(('/tmp/','foo/','bar.html#fragment1')).attempt_relative_url(href_context(('/tmp/','foo/','bar.html#fragment2')))=='#fragment1')
assert(href_context(('/tmp/','foo/','bar.html')).attempt_relative_url(href_context(('/tmp/','foo/','bar.html#fragment2')))=='')

assert(href_context(('/tmp/','fee/','bar.html#frag1')).attempt_relative_url(href_context(('/tmp/','foo/','bar.html#fragment2')))=='../fee/bar.html#frag1')

assert(href_context(('/tmp/','foo/','beer.html')).attempt_relative_url(href_context(('/tmp/','foo/','bar.html#fragment2')))=='beer.html')

assert(href_context(('/tmp/','foo/','beer.html#frag1')).attempt_relative_url(href_context(('/tmp/','foo/','bar.html#fragment2')))=='beer.html#frag1')


assert(href_context(('/tmp/','foo/','fubar/','beer.html')).attempt_relative_url(href_context(('/tmp/','foo/','bar.html#fragment2')))=='fubar/beer.html')


assert(href_context(('foo.html',)).attempt_relative_url(href_context(('foo.css',)))=='foo.html')

#foo=href_context(('foo.html',))
#bar=href_context(('foo.css',))
#import pdb
#pdb.set_trace()
#assert(foo.attempt_relative_url(bar)=='foo.html')


etxpath="/{http://foo/bar}a/c/{http://bar/foo}b/{http://foo/bar}d/@{http://foo/foo}c"


xpointer=canonicalize_path.canonical_url.etxpath2xpointer(None,etxpath)

print(xpointer)

