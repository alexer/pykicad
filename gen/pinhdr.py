import sys, os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import kicad

# Eagle uses oval pads for single-row headers
#pad_shape = 'oval'
#pad_size = (600, 1200)
#drill_size = 400

# Oval pads don't fit if there's more than 1 row
pad_shape = 'circle'
pad_size = (600, 600)
# For a square 0.025" pin, diameter is a bit more than 0.035"
drill_size = 400

def new_pad(position, name):
	# Variable: pad.name, pad.position
	# Settings: pad.shape, pad.size, pad.drill_size
	pad = kicad.Pad()
	pad.name = name
	pad.shape = pad_shape
	pad.size = pad_size
	pad.dsize = (0, 0)
	pad.orientation = 0
	pad.drill_offset = (0, 0)
	pad.drill_size = drill_size
	pad.type = 'STD'
	pad.layer_mask = kicad.LMASK_ALL_COPPER|kicad.L_TOP_SOLDERMASK|kicad.L_BOTTOM_SOLDERMASK|kicad.L_TOP_SILKSCREEN
	pad.net = 0
	pad.net_name = '""'
	pad.position = position
	return pad

def new_texte(type_, position, text):
	txt = kicad.Texte(type_)
	txt.text = text
	txt.position = position
	txt.size = (500, 500)
	txt.orientation = 0
	txt.thickness = 100
	txt.visible = True
	txt.mirrored = False
	txt.style = 'normal'
	txt.layer = 21
	return txt

def new_segment(p1, p2):
	seg = kicad.DrawSegment()
	seg.p1 = p1
	seg.p2 = p2
	seg.width = 80
	seg.layer = 21
	return seg

def new_module(cols, rows = 1):
	rowstr = {1: 'single', 2: 'double'}.get(rows, str(rows))
	short = 'MA%02d-%d' % (cols, rows)
	name = 'PINHDR-' + short

	xbase, ybase = -500 * (cols - 1), -500 * (rows - 1)
	minx, miny = xbase - 500, ybase - 500
	maxx, maxy = xbase + (cols - 1) * 1000 + 500, ybase + (rows - 1) * 1000 + 500
	minl, maxl = miny + 250, maxy - 250

	mod = kicad.Module()
	mod.name = name
	mod.position = (0, 0)
	mod.orientation = 0
	mod.layer = 15
	mod.last_edit_time = time.time()
	mod.timestamp = 0
	mod.locked = mod.placed = False
	mod.libref = name
	mod.doc = """Pin header, male, %d-pin, %s-row, straight, 0.1" spacing, 0.025" square pins""" % (cols, rowstr)
	mod.kws = [name, 'PINHDR-MA', 'PINHDR']
	mod.path = ''
	mod.r90 = mod.r180 = mod.xxx1 = 0
	mod.attrs = []
	mod.reference = new_texte('reference', (0, miny - 500), '"%s"' % (short, ))
	mod.value = new_texte('value', (0, maxy + 500), '"VAL**"')
	mod.text2 = None
	mod.draws = []
	mod.pads = []
	mod.shape3d = None

	for row in range(rows):
		for col in range(cols):
			pad_pos = (xbase + col * 1000, ybase + row * 1000)
			pad_name = '"%d"' % (col * rows + (rows - row), )
			mod.pads.append(new_pad(pad_pos, pad_name))

	mod.draws.append(new_segment((minx, minl), (minx, maxl)))
	for col in range(cols):
		base = minx + col * 1000
		mod.draws.extend((
			new_segment((base, minl), (base + 250, miny)),
			new_segment((base, maxl), (base + 250, maxy)),
			new_segment((base + 250, miny), (base + 750, miny)),
			new_segment((base + 250, maxy), (base + 750, maxy)),
			new_segment((base + 750, miny), (base + 1000, minl)),
			new_segment((base + 750, maxy), (base + 1000, maxl)),
		))
	mod.draws.append(new_segment((maxx, minl), (maxx, maxl)))

	return mod

def save_modules(f, *modules):
	print >>f, 'PCBNEW-LibModule-V1 ', time.strftime('%a %d %b %Y %H:%M:%S %Z')
	print >>f, '$INDEX'
	for module in modules:
		print >>f, module.name
	print >>f, '$EndINDEX'
	for module in modules:
		module.save(f)
	print >>f, '$EndLIBRARY'

if __name__ == '__main__':
	if len(sys.argv) > 1:
		mod = new_module(*map(int, sys.argv[1:]))
		save_modules(sys.stdout, mod)
	else:
		save_modules(sys.stdout, *[new_module(cols+1, rows+1) for cols in range(40) for rows in range(2)])

