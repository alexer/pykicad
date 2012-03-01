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


class Instruction:
	@classmethod
	def load(cls, f, *args):
		section = cls()
		try:
			section._load(f, *args)
		except:
			print 'In', cls.__name__
			raise
		return section

class Section(Instruction):
	section_name = None
	loaders = None
	default_loader = None
	def _init(self, *args):
		assert args == ('$' + self.section_name, )

	def _fini(self, *args):
		assert args == ('$End' + self.section_name, )

	def _load(self, f, *args):
		self._init(*args)
		while True:
			line = f.readline()
			if not line:
				print 'Unexpected EOF'
				sys.exit(1)
			line = line.rstrip('\n').split(None)
			if line[0] == '$End' + self.section_name:
				self._fini(*line)
				break
			loader = self.loaders.get(line[0], self.default_loader)
			if not loader:
				print 'Unknown section:', line[0]
				sys.exit(1)
			try:
				self._handle(loader(f, *line))
			except:
				print 'Handling', line
				raise

	def _handle(self, result):
		assert result is None


class Index(Section):
	section_name = 'INDEX'
	loaders = {}
	def __init__(self):
		self.module_names = []

	def default_loader(self, f, *line):
		self.module_names.append(' '.join(line))

	def dump(self):
		print 'Index:'
		for name in self.module_names:
			print '-', name

class Pad(Section):
	section_name = 'PAD'
	def __init__(self):
		self.loaders = {
			'Sh': self._load_shape,
			'Dr': self._load_drill,
			'At': self._load_attribute,
			'Ne': self._load_net,
			'Po': self._load_position,
		}

	def _load_shape(self, f, _op, name, shape, size_x, size_y, dsize_x, dsize_y, orient):
		self.name = name
		self.shape = {'C': 'circle', 'R': 'rectangle', 'O': 'oval', 'T': 'trapezoid'}[shape]
		self.size = int(size_x), int(size_y)
		self.dsize = int(dsize_x), int(dsize_y)
		self.orientation = int(orient)

	def _load_drill(self, f, _op, drill_x, offset_x, offset_y):
		self.drill_offset = int(offset_x), int(offset_y)
		self.drill_size = int(drill_x)

	def _load_attribute(self, f, _op, type_, xxx_, layer_mask):
		self.type = type_
		self.layer_mask = int(layer_mask, 16)
		assert xxx_ == 'N'

	def _load_net(self, f, _op, net, net_name):
		self.net = int(net)
		self.net_name = net_name

	def _load_position(self, f, _op, pos_x, pos_y):
		self.position = int(pos_x), int(pos_y)

	def dump(self):
		print '* Pad:'
		print '  - Name:', self.name
		print '  - Shape:', self.shape
		print '  - Size:', self.size
		print '  - Delta size:', self.dsize
		print '  - Orientation: %.1f°' % (self.orientation / 10., )
		print '  - Drill: Offset:', self.drill_offset, 'Width (???):', self.drill_size
		print '  - Type:', {'STD': 'Standard', 'SMD': 'SMD', 'CONN': 'Conn (???)', 'HOLE': 'Hole (not plated)'}[self.type]
		print '  - Layer mask:', '%08X' % (self.layer_mask, ), ', '.join(get_layers_from_mask(self.layer_mask))
		print '  - Net: Number:', self.net, 'Name:', self.net_name
		print '  - Position:', self.position

class Shape3D(Section):
	section_name = 'SHAPE3D'
	def __init__(self):
		self.name = None
		self.scale = None
		self.offset = None
		self.rotation = None
		self.loaders = {
			'Na': self._load_name,
			'Sc': self._load_scale,
			'Of': self._load_offset,
			'Ro': self._load_rotation,
		}

	def _load_name(self, f, _op, *name):
		assert self.name is None
		self.name = ' '.join(name)

	def _get_3d_loader(name):
		def loader(self, f, _op, *values):
			assert getattr(self, name) is None
			assert len(values) == 3
			setattr(self, name, map(float, values))
		return loader
	_load_scale = _get_3d_loader('scale')
	_load_offset = _get_3d_loader('offset')
	_load_rotation = _get_3d_loader('rotation')

	def dump(self):
		print '* 3D shape:'
		print '  - Name:', self.name
		for name in 'scale offset rotation'.split():
			print '  - %s:' % (name.title(), ), getattr(self, name)

class Texte(Instruction):
	def __init__(self, name):
		self.name = name

	def _load(self, f, _op, pos_x, pos_y, size_y, size_x, orient, thickness, mirror, visibility, layer, style, *text):
		ind = style.find('"')
		if len(style) > 1 and ind >= 0:
			assert ind in (0, 1)
			style, text = style[:ind], (style[ind:], ) + text
		self.text = ' '.join(text)
		self.position = int(pos_x), int(pos_y)
		self.size = int(size_x), int(size_y)
		self.orientation = int(orient)
		self.thickness = int(thickness)
		self.visible = {'V': True, 'I': False}[visibility]
		self.mirrored = {'M': True, 'N': False}[mirror]
		self.style = {'I': 'italic', 'N': 'normal', '': None}[style]
		self.layer = int(layer)

	@staticmethod
	def get_loader(name):
		def loader(f, *args):
			item = Texte(name)
			item._load(f, *args)
			return item
		return loader

	def dump(self):
		print '-', self.name.title(), 'text:', self.text
		print '  - Position:', self.position
		print '  - Size:', self.size
		print '  - Orientation: %.1f°' % (self.orientation / 10., )
		print '  - Thickness:', self.thickness
		print '  - Style:', ', '.join(({True: 'Visible', False: 'Invisible'}[self.visible], {True: 'Mirrored', False: 'Not Mirrored'}[self.mirrored], (self.style or 'unspecified').title()))
		print '  - Layer:', self.layer, layer_names[self.layer]

class DrawSegment(Instruction):
	def _load(self, f, _op, x1, y1, x2, y2, width, layer):
		self.p1 = int(x1), int(y1)
		self.p2 = int(x2), int(y2)
		self.width = int(width)
		self.layer = int(layer)

	def dump(self):
		print '- Line; from %r to %r, line width %d, layer' % (self.p1, self.p2, self.width), self.layer, layer_names[self.layer]

class DrawCircle(Instruction):
	def _load(self, f, _op, x1, y1, x2, y2, width, layer):
		self.center = int(x1), int(y1)
		self.outline = int(x2), int(y2)
		self.width = int(width)
		self.layer = int(layer)

	def dump(self):
		print '- Circle; center at %r, outline at %r, line width %d, layer' % (self.center, self.outline, self.width), self.layer, layer_names[self.layer]

class DrawArc(Instruction):
	def _load(self, f, _op, x1, y1, x2, y2, angle, width, layer):
		self.center = int(x1), int(y1)
		self.start = int(x2), int(y2)
		self.angle = int(angle)
		self.width = int(width)
		self.layer = int(layer)

	def dump(self):
		print '- Arc; center at %r, arc starts at %r, arc size %.1f°, line width %d, layer' % (self.center, self.start, self.angle / 10., self.width), self.layer, layer_names[self.layer]

class Module(Section):
	section_name = 'MODULE'
	def __init__(self):
		self.name = None
		self.timestamp = None
		self.reference = None
		self.value = None
		self.draws = []
		self.pads = []
		self.shape3d = None
		self.loaders = {
			'Po': self._load_position,
			'Li': self._load_libref,
			'Cd': self._load_doc,
			'Kw': self._load_keyword,
			'Sc': self._load_timestamp,
			'AR': self._load_path,
			'Op': self._load_cntrot,
			'At': self._load_attrs,
			'T0': self._load_reference,
			'T1': self._load_value,
			'DS': self._load_segment,
			'DC': self._load_circle,
			'DA': self._load_arc,
			'$PAD': Pad.load,
			'$SHAPE3D': Shape3D.load,
		}

	def _init(self, clsname, name):
		Section._init(self, clsname)
		self.name = name

	def _fini(self, endname, name):
		Section._fini(self, endname)
		assert name == self.name

	def _handle(self, result):
		if result is None:
			return
		elif isinstance(result, Pad):
			self.pads.append(result)
		elif isinstance(result, Shape3D):
			assert self.shape3d is None
			self.shape3d = result
		else:
			raise

	def _load_position(self, f, _op, pos_x, pos_y, orientation, layer, last_edit_time, timestamp_, status_txt):
		self.position = int(pos_x), int(pos_y)
		self.orientation = int(orientation)
		self.layer = int(layer)
		self.last_edit_time = int(last_edit_time, 16)
		if self.timestamp is None:
			self.timestamp = int(timestamp_, 16)
		else:
			assert self.timestamp == int(timestamp_, 16)
		self.locked = {'F': True, '~': False}[status_txt[0]]
		self.placed = {'F': True, '~': False}[status_txt[1]]
		assert len(status_txt) == 2

	def _load_libref(self, f, _op, libref):
		self.libref = libref

	def _load_doc(self, f, _op, *doc):
		self.doc = ' '.join(doc)

	def _load_keyword(self, f, _op, *kws):
		self.kws = kws

	def _load_timestamp(self, f, _op, timestamp_):
		if self.timestamp is None:
			self.timestamp = int(timestamp_, 16)
		else:
			assert self.timestamp == int(timestamp_, 16)

	def _load_path(self, f, _op, *path):
		self.path = ' '.join(path)

	def _load_cntrot(self, f, _op, r90, r180, xxx):
		self.r90 = r90
		self.r180 = r180
		self.xxx1 = xxx

	def _load_attrs(self, f, _op, *attrs):
		self.attrs = attrs

	def _get_texte_loader(name):
		def loader(self, f, *args):
			assert getattr(self, name) is None
			setattr(self, name, Texte.get_loader(name)(f, *args))
		return loader
	_load_reference = _get_texte_loader('reference')
	_load_value = _get_texte_loader('value')

	def _load_segment(self, f, *args):
		self.draws.append(DrawSegment.load(f, *args))

	def _load_circle(self, f, *args):
		self.draws.append(DrawCircle.load(f, *args))

	def _load_arc(self, f, *args):
		self.draws.append(DrawArc.load(f, *args))

	def dump(self):
		print 'Module:', self.name
		print '- Position on board:', self.position
		print '- Orientation: %.1f°' % (self.orientation/10., )
		print '- Layer:', self.layer, layer_names[self.layer]
		print '- Last edit time:', timestamp(self.last_edit_time)
		print '- Timestamp used for logical links (???):', timestamp(self.timestamp)
		print '- Status:', ', '.join(({True: 'Locked', False: 'Not Locked'}[self.locked], {True: 'Placed', False: 'Not Placed'}[self.placed]))
		print '- Library reference:', self.libref
		print '- Module description:', self.doc
		print '- Keywords to select the module in library:', self.kws
		print '- AR (???) / Path (???):', self.path
		print '- Automatic placement costs:'
		print '  - 90 degrees rotation (Horizontal <-> Vertical):', self.r90
		print '  - 180 degrees rotation (UP <-> Down):', self.r180
		print '  - ???:', self.xxx1
		self.reference.dump()
		self.value.dump()
		for draw in self.draws:
			draw.dump()
		for pad in self.pads:
			pad.dump()
		self.shape3d.dump()

class ModuleLibrary(Section):
	section_name = 'LIBRARY'
	loaders = {
		'$INDEX': Index.load,
		'$MODULE': Module.load,
	}
	def __init__(self):
		self.index = None
		self.modules = []

	def _handle(self, result):
		if isinstance(result, Index):
			assert self.index is None
			self.index = result
		elif isinstance(result, Module):
			self.modules.append(result)
		else:
			raise

	def dump(self):
		self.index.dump()
		for module in self.modules:
			module.dump()

def load_mod(f):
	header = f.readline().rstrip('\n')
	magic, created = header.split(None, 1)
	assert magic == 'PCBNEW-LibModule-V1'
	print 'Creation time:', created
	result = ModuleLibrary.load(f, '$LIBRARY')
	line = f.readline()
	assert line == ''
	return result

loaders = {
	'mod': load_mod,
}

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print 'usage: %s FILE' % (sys.argv[0], )
		sys.exit(1)

	fname = sys.argv[1]
	ext = os.path.splitext(fname)[1][1:]
	loader = loaders.get(ext)

	if not loader:
		print 'Unknown file extension! Should be one of:', ', '.join('.' + ext for ext in dumpers)
		sys.exit(1)

	with file(fname) as f:
		result = loader(f)
		result.dump()

