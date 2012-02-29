#! /usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo
from gtk import gdk
import math

import kicad

# Create a GTK+ widget on which we will draw using Cairo
class CairoGTK(gtk.DrawingArea):
	# Draw in response to an expose-event
	__gsignals__ = {'expose-event': 'override'}
	def __init__(self, modlib, index = 0):
		gtk.DrawingArea.__init__(self)

		self.modlib = modlib
		self.index = index

		self.next_module()

		#self.connect_after("realize", self._init)
		#self.connect("configure_event", self._reshape)
		self.connect("button_press_event", self._mouseButton)
		self.connect("button_release_event", self._mouseButton)
		#self.connect("motion_notify_event", self._mouseMotion)
		self.connect("scroll_event", self._mouseScroll)

		self.set_events(self.get_events() | gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK)#|gdk.POINTER_MOTION_MASK|gdk.POINTER_MOTION_HINT_MASK)

	def next_module(self):
		self.set_model(self.modlib.modules[self.index % len(self.modlib.modules)])
		self.index += 1

	def set_model(self, model):
		print model.name
		self.model = model

		self.modelbounds = get_module_size(model)
		(self.minx, self.miny), (self.maxx, self.maxy) = self.modelbounds

		self.modelsize = (self.maxx - self.minx, self.maxy - self.miny)
		self.modelwidth, self.modelheight = self.modelsize

		self.xpos = -self.minx
		self.ypos = -self.miny
		self.zoomscale = 1

	def zoom(self, zamt, center):
		self.zoomscale *= zamt

		old_pos = self.scr2mdl(center)
		self._rescale()
		new_pos = self.scr2mdl(center)

		self.xpos += new_pos[0] - old_pos[0]
		self.ypos += new_pos[1] - old_pos[1]

		self.redraw()

	def pan(self, (xamt, yamt)):
		self.xpos, self.ypos = (self.xpos + self.scr2mdl_l(xamt), self.ypos + self.scr2mdl_l(yamt))

		self.redraw()

	def _mouseButton(self, widget, event):
		if event.button == 1:
			if event.type == gdk.BUTTON_PRESS:
				self.click = event.x, event.y
			elif event.type == gdk.BUTTON_RELEASE:
				rel = (event.x - self.click[0], event.y - self.click[1])
				self.click = None
				self.pan(rel)
		elif event.button == 2 and event.type == gdk.BUTTON_RELEASE:
			self.next_module()
			self._reshape()
			self.redraw()
		#if (event.state & gdk.BUTTON1_MASK) == gdk.BUTTON1_MASK:
		#	currently down

	def _mouseScroll(self, widget, event):
		zamt = 0.5 if (event.direction == gdk.SCROLL_UP) else 2

		self.zoom(zamt, (event.x, event.y))

	def _reshape(self):
		self.size = self.window.get_size()
		self.width, self.height = self.size

		self._rescale()


	def _get_scale(self, src, dst):
		(sw, sh) = src
		(dw, dh) = dst
		return min(float(dw) / sw, float(dh) / sh)

	def _rescale(self):
		self.modelscale = self._get_scale(self.modelsize, self.size)
		self.scale = self.modelscale * self.zoomscale


	def mdl2scr(self, (x, y)):
		return ((x - self.xpos) * self.scale, (y - self.ypos) * self.scale)

	def scr2mdl(self, (x, y)):
		return (x / self.scale + self.xpos, (y / self.scale + self.ypos))

	def mdl2scr_l(self, l):
		return l * self.scale

	def scr2mdl_l(self, l):
		return l / self.scale


	# Handle the expose-event by drawing
	def do_expose_event(self, event):
		if self.window.get_size() != self.size:
			self._reshape()

		self.draw(event.area.x, event.area.y, event.area.width, event.area.height)

	def redraw(self):
		self.draw(0, 0, *self.size)

	def draw(self, x, y, w, h):
		# Create the cairo context
		cr = self.window.cairo_create()

		# Restrict Cairo to the exposed area; avoid extra work
		cr.rectangle(x, y, w, h)
		cr.clip()

		# Fill the background with black
		cr.set_source_rgb(0.0, 0.0, 0.0)
		cr.rectangle(0, 0, w, h)
		cr.fill()

		cr.set_line_width(1.0)

		self.raw_draw(cr)

	def raw_draw(self, cr):
		print self.xpos, self.ypos, self.zoomscale, self.scale

		cr.scale(self.scale, self.scale)
		cr.translate(self.xpos, self.ypos)

		cr.set_source_rgb(1.0, 0.0, 0.0)
		cr.set_line_width(cr.device_to_user_distance(1, 1)[0])

		cr.move_to(*cr.device_to_user_distance(0, -10))
		cr.rel_line_to(*cr.device_to_user_distance(0, 20))
		cr.move_to(*cr.device_to_user_distance(-10, 0))
		cr.rel_line_to(*cr.device_to_user_distance(20, 0))
		cr.stroke()

		draw(cr, self.model)

def get_module_size(mod):
	points = iter_module_points(mod)
	minx, miny = maxx, maxy = points.next()
	for x, y in points:
		minx = min(minx, x)
		miny = min(miny, y)
		maxx = max(maxx, x)
		maxy = max(maxy, y)
	return (minx, miny), (maxx, maxy)

def iter_module_points(mod):
	for item in mod.draws:
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
	for pad in mod.pads:
		if pad.shape in ('rectangle', 'circle', 'oval'):
			yield pad.position[0] - pad.size[0]/2., pad.position[1] - pad.size[1]/2.
			yield pad.position[0] + pad.size[0]/2., pad.position[1] + pad.size[1]/2.
		else:
			raise ValueError, 'Unknown shape'

def draw(cr, model):
	draw_pads(cr, model.pads)
	draw_silk(cr, model.draws)

def draw_silk(cr, items):
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
			print item.center, item.start, math.degrees(start_angle)
			cr.arc(item.center[0], item.center[1], math.sqrt((item.center[0]-item.start[0])**2 + (item.center[1]-item.start[1])**2), start_angle, start_angle + math.radians(item.angle/10.))
		else:
			raise TypeError, 'Unknown shape'
		cr.stroke()

	cr.pop_group_to_source()
	cr.paint_with_alpha(0.8)

def draw_pads(cr, pads):
	cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
	cr.set_source_rgba(160/255., 160/255., 0.0, 0.8)

	for pad in pads:
		if pad.shape == 'rectangle':
			cr.rectangle(pad.position[0] - pad.size[0]/2., pad.position[1] - pad.size[1]/2., pad.size[0], pad.size[1])
		elif pad.shape == 'circle':
			assert pad.size[0] == pad.size[1]
			cr.arc(pad.position[0], pad.position[1], pad.size[0]/2., 0, 2 * math.pi)
		elif pad.shape == 'oval':
			r = min(pad.size)/2.
			xsize = max(0, pad.size[0] - pad.size[1])
			ysize = max(0, pad.size[1] - pad.size[0])
			cr.move_to(pad.position[0] - pad.size[0]/2., pad.position[1] + ysize/2.)
			cr.arc(pad.position[0] - xsize/2., pad.position[1] - ysize/2., r, math.pi, 3 * math.pi/2.)
			cr.arc(pad.position[0] + xsize/2., pad.position[1] - ysize/2., r, 3 * math.pi/2., 2 * math.pi)
			cr.arc(pad.position[0] + xsize/2., pad.position[1] + ysize/2., r, 0, math.pi/2.)
			cr.arc(pad.position[0] - xsize/2., pad.position[1] + ysize/2., r, math.pi/2., math.pi)
			cr.new_sub_path()
		else:
			raise ValueError, 'Unknown shape'
		cr.arc(pad.position[0], pad.position[1], pad.drill_size/2., 0, 2 * math.pi)
		cr.fill()

# GTK mumbo-jumbo to show the widget in a window and quit when it's closed
def run(widget):
	window = gtk.Window()
	window.connect("delete-event", gtk.main_quit)
	widget.show()
	window.add(widget)
	window.present()
	widget._reshape()
	gtk.main()

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

	run(CairoGTK(modlib, index))

