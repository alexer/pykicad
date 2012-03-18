#! /usr/bin/env python
import gtk
from gtk import gdk
import cairo
import math

from cairogtk import CairoGTK, BaseDrawing
import kicad

class KicadDrawing(BaseDrawing):
	def __init__(self, module):
		self.module = module

	def get_size(self):
		points = self.points()
		minx, miny = maxx, maxy = points.next()
		for x, y in points:
			minx = min(minx, x)
			miny = min(miny, y)
			maxx = max(maxx, x)
			maxy = max(maxy, y)
		return (minx, miny), (maxx, maxy)

	def points(self):
		for item in self.module.draws:
			if isinstance(item, kicad.DrawSegment):
				(x1, y1), (x2, y2) = item.p1, item.p2
				yield min(x1, x2) - item.width, min(y1, y2) - item.width
				yield max(x1, x2) + item.width, max(y1, y2) + item.width
			elif isinstance(item, kicad.DrawCircle):
				r = math.sqrt((item.center[0]-item.outline[0])**2 + (item.center[1]-item.outline[1])**2)
				yield item.center[0] - r - item.width, item.center[1] - r - item.width
				yield item.center[0] + r + item.width, item.center[1] + r + item.width
			elif isinstance(item, kicad.DrawArc):
				item.dump()
				r = math.sqrt((item.center[0]-item.start[0])**2 + (item.center[1]-item.start[1])**2)
				yield item.center[0] - r - item.width, item.center[1] - r - item.width
				yield item.center[0] + r + item.width, item.center[1] + r + item.width
			else:
				raise TypeError, 'Unknown shape'
		for pad in self.module.pads:
			if pad.shape in ('rectangle', 'circle', 'oval'):
				yield pad.position[0] - pad.size[0]/2., pad.position[1] - pad.size[1]/2.
				yield pad.position[0] + pad.size[0]/2., pad.position[1] + pad.size[1]/2.
			else:
				raise ValueError, 'Unknown shape'

	def draw(self, cr):
		# Draw red cross at origo
		cr.set_source_rgb(1.0, 0.0, 0.0)
		cr.set_line_width(cr.device_to_user_distance(1, 1)[0])
		cr.move_to(*cr.device_to_user_distance(0, -10))
		cr.rel_line_to(*cr.device_to_user_distance(0, 20))
		cr.move_to(*cr.device_to_user_distance(-10, 0))
		cr.rel_line_to(*cr.device_to_user_distance(20, 0))
		cr.stroke()

		self.draw_pads(cr, self.module.pads)
		self.draw_silk(cr, self.module.draws)

	def draw_silk(self, cr, items):
		cr.set_line_cap(cairo.LINE_CAP_ROUND)

		cr.push_group()

		cr.set_source_rgb(0.0, 200/255., 200/255.)
		for item in items:
			cr.set_line_width(item.width)
			if isinstance(item, kicad.DrawSegment):
				cr.move_to(*item.p1)
				cr.line_to(*item.p2)
			elif isinstance(item, kicad.DrawCircle):
				cr.arc(item.center[0], item.center[1], math.sqrt((item.center[0]-item.outline[0])**2 + (item.center[1]-item.outline[1])**2), 0, 2 * math.pi)
			elif isinstance(item, kicad.DrawArc):
				start_angle = math.atan2(item.start[1]-item.center[1], item.start[0]-item.center[0])
				print item.center, item.start, math.degrees(start_angle), item.angle/10.
				(cr.arc if item.angle >= 0 else cr.arc_negative)(item.center[0], item.center[1], math.sqrt((item.center[0]-item.start[0])**2 + (item.center[1]-item.start[1])**2), start_angle, start_angle + math.radians(item.angle/10.))
			else:
				raise TypeError, 'Unknown shape'
			cr.stroke()

		cr.pop_group_to_source()
		cr.paint_with_alpha(0.8)

	def draw_pads(self, cr, pads):
		cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)

		cr.push_group()

		cr.set_source_rgb(160/255., 160/255., 0.0)
		for pad in pads:
			cr.save()
			cr.translate(pad.position[0], pad.position[1])
			cr.rotate(-math.radians(pad.orientation/10.))
			cr.translate(-pad.position[0], -pad.position[1])
			if pad.type == 'SMD':
				pad_center = pad.position[0], pad.position[1]
			else:
				pad_center = pad.position[0] + pad.drill_offset[0], pad.position[1] + pad.drill_offset[1]
			if pad.shape == 'rectangle':
				cr.rectangle(pad_center[0] - pad.size[0]/2., pad_center[1] - pad.size[1]/2., pad.size[0], pad.size[1])
			elif pad.shape == 'circle':
				assert pad.size[0] == pad.size[1]
				cr.arc(pad_center[0], pad_center[1], pad.size[0]/2., 0, 2 * math.pi)
			elif pad.shape == 'oval':
				r = min(pad.size)/2.
				xsize = max(0, pad.size[0] - pad.size[1])
				ysize = max(0, pad.size[1] - pad.size[0])
				cr.move_to(pad_center[0] - pad.size[0]/2., pad_center[1] + ysize/2.)
				cr.arc(pad_center[0] - xsize/2., pad_center[1] - ysize/2., r, math.pi, 3 * math.pi/2.)
				cr.arc(pad_center[0] + xsize/2., pad_center[1] - ysize/2., r, 3 * math.pi/2., 2 * math.pi)
				cr.arc(pad_center[0] + xsize/2., pad_center[1] + ysize/2., r, 0, math.pi/2.)
				cr.arc(pad_center[0] - xsize/2., pad_center[1] + ysize/2., r, math.pi/2., math.pi)
				cr.new_sub_path()
			else:
				raise ValueError, 'Unknown shape'
			cr.restore()
			if pad.type != 'SMD':
				cr.arc(pad.position[0], pad.position[1], pad.drill_size/2., 0, 2 * math.pi)
			cr.fill()

		cr.pop_group_to_source()
		cr.paint_with_alpha(0.8)

class ModuleBrowser(CairoGTK):
	def __init__(self, modlib, index):
		CairoGTK.__init__(self, KicadDrawing(modlib.modules[index]))
		self.modlib = modlib
		self.index = index

	def next_module(self):
		self.index += 1
		self.set_model(KicadDrawing(self.modlib.modules[self.index % len(self.modlib.modules)]))

	def _mouseButton(self, widget, event):
		CairoGTK._mouseButton(self, widget, event)
		if event.button == 2 and event.type == gdk.BUTTON_RELEASE:
			self.next_module()
			self._reshape()
			self.redraw()

if __name__ == "__main__":
	import sys

	try:
		library, module = sys.argv[1:3]
	except:
		library, module = sys.argv[1], None

	with file(library) as f:
		modlib = kicad.load_mod(f)
		if module:
			index = [ind for ind, mod in enumerate(modlib.modules) if mod.name == module][0]
		else:
			index = 0

	widget = ModuleBrowser(modlib, index)

	window = gtk.Window()
	window.connect("delete-event", gtk.main_quit)
	widget.show()
	window.add(widget)
	window.present()
	widget._reshape()

	gtk.main()

