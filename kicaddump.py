#! /usr/bin/env python
import sys, os
import kicad

loaders = {
	'mod': kicad.load_mod,
}

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print 'usage: %s FILE' % (sys.argv[0], )
		sys.exit(1)

	fname = sys.argv[1]
	ext = os.path.splitext(fname)[1][1:]
	loader = loaders.get(ext)

	if not loader:
		print 'Unknown file extension! Should be one of:', ', '.join('.' + ext for ext in loaders)
		sys.exit(1)

	with file(fname) as f:
		result = loader(f)
		result.dump()

