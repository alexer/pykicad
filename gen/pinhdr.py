#! /usr/bin/env python
import sys, os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import kicad

mm2u = lambda val: val * 1000000
um2u = lambda val: val * 1000

in2u = lambda val: val * 25400000
mil2u = lambda val: val * 25400

u2mm = lambda val: val / 1000000.
u2um = lambda val: val / 1000.

u2in = lambda val: val / 25400000.
u2mil = lambda val: val / 25400.

u2kicad = lambda val: int(val / 2540.)
p2kicad = lambda (x, y): (u2kicad(x), u2kicad(y))

u2ins = lambda val: ('%f' % u2in(val)).rstrip('0') + '"'
u2mms = lambda val: ('%f' % u2mm(val)).rstrip('0') + 'mm'

# If you change the pitch, remember to check the results
pitch = mil2u(100)
notch = mil2u(20)
# Oval pads don't fit if there's more than 1 row
pad_shape = 'circle'
pad_size = (mil2u(60), mil2u(60))
# For a square 0.025" pin, diameter is a bit more than 0.035"
drill_size = mil2u(40)

# Eagle uses oval pads for single-row headers
#pad_shape = 'oval'
#pad_size = (mil2u(60), mil2u(120))
#drill_size = mil2u(40)
#notch = mil2u(25)

def new_pad(position, name):
	# Variable: pad.name, pad.position
	# Settings: pad.shape, pad.size, pad.drill_size
	pad = kicad.Pad()
	pad.name = name
	pad.shape = pad_shape
	pad.size = p2kicad(pad_size)
	pad.dsize = (0, 0)
	pad.orientation = 0
	pad.drill_offset = (0, 0)
	pad.drill_size = u2kicad(drill_size)
	pad.type = 'STD'
	pad.layer_mask = kicad.LMASK_ALL_COPPER|kicad.L_TOP_SOLDERMASK|kicad.L_BOTTOM_SOLDERMASK|kicad.L_TOP_SILKSCREEN
	pad.net = 0
	pad.net_name = '""'
	pad.position = p2kicad(position)
	return pad

def new_texte(type_, position, text):
	txt = kicad.Texte(type_)
	txt.text = text
	txt.position = p2kicad(position)
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
	seg.p1 = p2kicad(p1)
	seg.p2 = p2kicad(p2)
	seg.width = 80
	seg.layer = 21
	return seg

def new_module(cols, rows = 1):
	rowstr = {1: 'single', 2: 'double', 3: 'triple'}.get(rows, str(rows))
	short = 'M%02dX%d' % (cols, rows)
	name = 'PINHDR-%s-%s-PTH-S' % (short, u2mms(pitch).upper())

	pitch2 = pitch/2
	xbase, ybase = -pitch2 * (cols - 1), -pitch2 * (rows - 1)
	minx, miny = xbase - pitch2, ybase - pitch2
	maxx, maxy = xbase + (cols - 1) * pitch + pitch2, ybase + (rows - 1) * pitch + pitch2
	minl, maxl = miny + notch, maxy - notch

	mod = kicad.Module()
	mod.name = name
	mod.position = (0, 0)
	mod.orientation = 0
	mod.layer = 15
	mod.last_edit_time = time.time()
	mod.timestamp = 0
	mod.locked = mod.placed = False
	mod.libref = name
	mod.doc = """Pin header, male, %d-pin, %s-row, %s spacing, through-hole, straight, 0.025" square pins""" % (cols, rowstr, u2ins(pitch))
	mod.kws = [name, 'PINHDR-M', 'PINHDR']
	mod.path = ''
	mod.r90 = mod.r180 = mod.xxx1 = 0
	mod.attrs = []
	mod.reference = new_texte('reference', (0, miny - pitch2), '"%s"' % (short, ))
	mod.value = new_texte('value', (0, maxy + pitch2), '"VAL**"')
	mod.text2 = None
	mod.draws = []
	mod.pads = []
	mod.shape3d = None

	for col in range(cols):
		for row in range(rows - 1, -1, -1):
			pad_pos = (xbase + col * pitch, ybase + row * pitch)
			pad_name = '"%d"' % (col * rows + (rows - row), )
			mod.pads.append(new_pad(pad_pos, pad_name))

	mod.draws.append(new_segment((minx, minl), (minx, maxl)))
	for col in range(cols):
		base = minx + col * pitch
		mod.draws.extend((
			new_segment((base, minl), (base + notch, miny)),
			new_segment((base, maxl), (base + notch, maxy)),
			new_segment((base + notch, miny), (base + (pitch - notch), miny)),
			new_segment((base + notch, maxy), (base + (pitch - notch), maxy)),
			new_segment((base + (pitch - notch), miny), (base + pitch, minl)),
			new_segment((base + (pitch - notch), maxy), (base + pitch, maxl)),
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
		save_modules(sys.stdout, *[new_module(cols+1, rows+1) for cols in range(40) for rows in range(3)])

