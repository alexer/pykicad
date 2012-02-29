# -!- encoding: utf-8 -!-
import sys, os, time

def timestamp(t = None):
	if t == 0:
		return '-'
	return '%04d-%02d-%02d %02d:%02d:%02d' % time.localtime(t)[:6]


# Copper layers 0-15; 0=back/bottom; 15=front/top
layers = {
	0: 'Bottom copper (0)',
	1: 'Internal copper (1)',
	2: 'Internal copper (2)',
	3: 'Internal copper (3)',
	4: 'Internal copper (4)',
	5: 'Internal copper (5)',
	6: 'Internal copper (6)',
	7: 'Internal copper (7)',
	8: 'Internal copper (8)',
	9: 'Internal copper (9)',
	10: 'Internal copper (10)',
	11: 'Internal copper (11)',
	12: 'Internal copper (12)',
	13: 'Internal copper (13)',
	14: 'Internal copper (14)',
	15: 'Top copper (15)',

	16: 'Bottom adhesive',
	17: 'Top adhesive',
	18: 'Bottom solderpaste',
	19: 'Top solderpaste',
	20: 'Bottom silkscreen',
	21: 'Top silkscreen',
	22: 'Bottom soldermask',
	23: 'Top soldermask',
	24: 'Draw',
	25: 'Comment',
	26: 'Eco1',
	27: 'Eco2',
	28: 'Edge',
}

BOTTOM_LAYER, TOP_LAYER = 1, 16

layers = []

for layer in range(16):
	layers.append((layer, 'copper', layer + 1))

for i, name in enumerate('adhesive solderpaste silkscreen soldermask'.split()):
	layers.append((16 + i*2, name, BOTTOM_LAYER))
	layers.append((16 + i*2 + 1, name, TOP_LAYER))

layers.extend([
	(24, 'draw', None),
	(25, 'comment', None),
	(26, 'eco1', None),
	(27, 'eco2', None),
	(28, 'edge', None),
	(29, 'unused 29', None),
	(30, 'unused 30', None),
	(31, 'unused 31', None),
])

layer_names = {}
for lnum, name, clnum in layers:
	clname = {BOTTOM_LAYER: 'bottom', TOP_LAYER: 'top', None: None}.get(clnum)
	layer_variable = ((clname.upper() + '_') if clname else '') + name.upper() + ('_' + str(clnum) if clnum and not clname else '')
	layer_name = (((clname + ' ') if clname else '') + name + (' ' + str(clnum) if clnum and not clname else '')).title()
	layer_names[lnum] = layer_name
	globals()['LNUM_' + layer_variable] = lnum
	globals()['L_' + layer_variable] = (1 << lnum)


LMASK_ALL             = 0x1FFFFFFF
LMASK_NON_COPPER      = 0x1FFF0000
LMASK_ALL_COPPER      = 0x0000FFFF
LMASK_INTERNAL_COPPER = 0x00007FFE
LMASK_EXTERNAL_COPPER = 0x00008001

layer_masks = [
	(0x1FFFFFFF, 'All'),
	(0x1FFF0000, 'All non-copper'),
	(0x0000FFFF, 'All copper'),
	(0x00007FFE, 'All internal copper'),
	(0x00008001, 'All external copper'),
	(0x00030000, 'All adhesive'),
	(0x000c0000, 'All solderpaste'),
	(0x00300000, 'All silkscreen'),
	(0x00c00000, 'All soldermask'),
]


def get_layers_from_mask(mask):
	names = []

	for lmask, title in layer_masks:
		if (mask & lmask) == lmask:
			mask ^= lmask
			names.append(title)

	for lnum, name, clnum in layers:
		if mask & (1 << lnum):
			names.append(layer_names[lnum])

	return names


def dump_mod_index(f, ):
	print 'Index / Modules contained in this file:'
	while True:
		line = f.readline()
		if not line:
			print 'Unexpected EOF'
			sys.exit(1)
		line = line.rstrip('\n')
		if line == '$EndINDEX':
			break
		print '- ', line

def dump_mod_module_position(f, pos_x, pos_y, orientation, layer, last_edit_time, timestamp_, status_txt):
	print '- Position on board:', int(pos_x), int(pos_y)
	print '- Orientation: %.1f°' % (float(orientation)/10, )
	print '- Layer:', int(layer), layer_names[int(layer)]
	print '- Last edit time:', timestamp(int(last_edit_time, 16))
	print '- Timestamp used for logical links (???):', timestamp(int(timestamp_, 16))
	print '- Status:', ', '.join(({'F': 'Locked', '~': 'Not Locked'}[status_txt[0]], {'F': 'Placed', '~': 'Not Placed'}[status_txt[1]]))
	assert len(status_txt) == 2

def dump_mod_module_libref(f, libref):
	print '- Library reference:', libref

def dump_mod_module_doc(f, *doc):
	print '- Module description:', ' '.join(doc)

def dump_mod_module_keyword(f, kw):
	print '- Keywords to select the module in library:', kw

def dump_mod_module_timestamp(f, timestamp_):
	print '- Timestamp used for logical links AGAIN (???):', timestamp(int(timestamp_, 16))

def dump_mod_module_path(f, *path):
	print '- AR (???) / Path (???):', ' '.join(path)

def dump_mod_module_cntrot(f, r90, r180, xxx):
	print '- Automatic placement costs:'
	print '  - 90 degrees rotation (Horizontal <-> Vertical):', r90
	print '  - 180 degrees rotation (UP <-> Down):', r180
	print '  - ???:', xxx

def dump_mod_module_texte(title):
	def dumper(f, pos_x, pos_y, size_y, size_x, orient, thickness, mirror, visibility, layer, style, *text):
		ind = style.find('"')
		if len(style) > 1 and ind >= 0:
			assert ind in (0, 1)
			style, text = style[:ind], (style[ind:], ) + text
		print '- Module', title, 'text:', ' '.join(text)
		print '  - Position:', pos_x, pos_y
		print '  - Size:', size_x, size_y
		print '  - Orientation: %.1f°' % (float(orient) / 10, )
		print '  - Thickness:', thickness
		print '  - Style:', ', '.join(({'V': 'Visible', 'I': 'Invisible'}[visibility], {'M': 'Mirrored', 'N': 'Not Mirrored'}[mirror], {'I': 'Italic', 'N': 'Normal', '': 'Unspecified'}[style]))
		print '  - Layer:', int(layer), layer_names[int(layer)]
	return dumper

def dump_mod_module_segment(f, x1, y1, x2, y2, width, layer):
	print '- Line; from %r to %r, line width %d, layer' % ((int(x1), int(y1)), (int(x2), int(y2)), int(width)), int(layer), layer_names[int(layer)]

def dump_mod_module_circle(f, x1, y1, x2, y2, width, layer):
	print '- Circle; center at %r, outline at %r, line width %d, layer' % ((int(x1), int(y1)), (int(x2), int(y2)), int(width)), int(layer), layer_names[int(layer)]

def dump_mod_module_arc(f, x1, y1, x2, y2, angle, width, layer):
	print '- Arc; center at %r, arc starts at %r, arc size %.1f°, line width %d, layer' % ((int(x1), int(y1)), (int(x2), int(y2)), float(angle) / 10, int(width)), int(layer), layer_names[int(layer)]

def dump_mod_module_pad_shape(f, name, shape, size_x, size_y, dsize_x, dsize_y, orient):
	print '  - Name:', name
	print '  - Shape:', {'C': 'circle', 'R': 'rectangle', 'O': 'oval', 'T': 'trapezoid'}[shape]
	print '  - Size:', size_x, size_y
	print '  - Delta size:', dsize_x, dsize_y
	print '  - Orientation: %.1f°' % (float(orient) / 10, )

def dump_mod_module_pad_drill(f, drill_x, offset_x, offset_y):
	print '  - Drill: Offset:', offset_x, offset_y, 'Width (???):', drill_x

def dump_mod_module_pad_attribute(f, type_, xxx_, layer_mask):
	print '  - Type:', {'STD': 'Standard', 'SMD': 'SMD', 'CONN': 'Conn (???)', 'HOLE': 'Hole (not plated)'}[type_]
	assert xxx_ == 'N'
	print '  - Layer mask:', layer_mask, ', '.join(get_layers_from_mask(int(layer_mask, 16)))

def dump_mod_module_pad_net(f, net, net_name):
	print '  - Net: Number:', net, 'Name:', net_name

def dump_mod_module_pad_position(f, pos_x, pos_y):
	print '  - Position:', pos_x, pos_y

mod_module_pad_dumpers = {
	'Sh': dump_mod_module_pad_shape,
	'Dr': dump_mod_module_pad_drill,
	'At': dump_mod_module_pad_attribute,
	'Ne': dump_mod_module_pad_net,
	'Po': dump_mod_module_pad_position,
}

def dump_mod_module_pad(f):
	print '- Definition for pad:'
	while True:
		line = f.readline()
		if not line:
			print 'Unexpected EOF'
			sys.exit(1)
		line = line.rstrip('\n').split(None)
		if line[0] == '$EndPAD':
			break
		mod_module_pad_dumper = mod_module_pad_dumpers.get(line[0])
		if not mod_module_pad_dumper:
			print 'Unknown section:', line[0]
			sys.exit(1)
		mod_module_pad_dumper(f, *line[1:])

def dump_mod_module_shape3d_name(f, *name):
	print '  - Name:', ' '.join(name)

def dump_mod_module_shape3d_3d(title):
	def dumper(f, x, y, z):
		print '  - %s:' % (title.title(), ), x, y, z
	return dumper

mod_module_shape3d_dumpers = {
	'Na': dump_mod_module_shape3d_name,
	'Sc': dump_mod_module_shape3d_3d('scale'),
	'Of': dump_mod_module_shape3d_3d('offset'),
	'Ro': dump_mod_module_shape3d_3d('rotation'),
}

def dump_mod_module_shape3d(f):
	print '- Definition for 3d shape:'
	while True:
		line = f.readline()
		if not line:
			print 'Unexpected EOF'
			sys.exit(1)
		line = line.rstrip('\n').split(None)
		if line[0] == '$EndSHAPE3D':
			break
		mod_module_shape3d_dumper = mod_module_shape3d_dumpers.get(line[0])
		if not mod_module_shape3d_dumper:
			print 'Unknown section:', line[0]
			sys.exit(1)
		mod_module_shape3d_dumper(f, *line[1:])

mod_module_dumpers = {
	'Po': dump_mod_module_position,
	'Li': dump_mod_module_libref,
	'Cd': dump_mod_module_doc,
	'Kw': dump_mod_module_keyword,
	'Sc': dump_mod_module_timestamp,
	'AR': dump_mod_module_path,
	'Op': dump_mod_module_cntrot,
	'T0': dump_mod_module_texte('reference'),
	'T1': dump_mod_module_texte('value'),
	'DS': dump_mod_module_segment,
	'DC': dump_mod_module_circle,
	'DA': dump_mod_module_arc,
	'$PAD': dump_mod_module_pad,
	'$SHAPE3D': dump_mod_module_shape3d,
}

def dump_mod_module(f, name):
	print 'Definition for module %s:' % (name, )
	while True:
		line = f.readline()
		if not line:
			print 'Unexpected EOF'
			sys.exit(1)
		line = line.rstrip('\n').split(None)
		if line[0] == '$EndMODULE':
			assert line[1] == name
			break
		mod_module_dumper = mod_module_dumpers.get(line[0])
		if not mod_module_dumper:
			print 'Unknown section:', line[0]
			sys.exit(1)
		mod_module_dumper(f, *line[1:])

def dump_mod_end(f):
	line = f.readline()
	assert line == ''

mod_dumpers = {
	'$INDEX': dump_mod_index,
	'$MODULE': dump_mod_module,
	'$EndLIBRARY': dump_mod_end,
}

def dump_mod(f):
	header = f.readline().rstrip('\n')
	magic, created = header.split(None, 1)
	assert magic == 'PCBNEW-LibModule-V1'
	print 'Creation time:', created
	while True:
		line = f.readline()
		if not line:
			break
		line = line.rstrip('\n').split(None)
		mod_dumper = mod_dumpers.get(line[0])
		if not mod_dumper:
			print 'Unknown section:', line[0]
			sys.exit(1)
		mod_dumper(f, *line[1:])

dumpers = {
	'mod': dump_mod,
}

if len(sys.argv) < 2:
	print 'usage: %s FILE' % (sys.argv[0], )
	sys.exit(1)

fname = sys.argv[1]
ext = os.path.splitext(fname)[1][1:]
dumper = dumpers.get(ext)

if not dumper:
	print 'Unknown file extension! Should be one of:', ', '.join('.' + ext for ext in dumpers)
	sys.exit(1)

with file(fname) as f:
	dumper(f)

