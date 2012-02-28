#! /usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo
from gtk import gdk
import math

# Create a GTK+ widget on which we will draw using Cairo
class CairoGTK(gtk.DrawingArea):
	# Draw in response to an expose-event
	__gsignals__ = {'expose-event': 'override'}
	def __init__(self):
		gtk.DrawingArea.__init__(self)

		self.modelbounds = ((-1350, -1350), (1350, 1350))
		(self.minx, self.miny), (self.maxx, self.maxy) = self.modelbounds

		self.modelsize = (self.maxx - self.minx, self.maxy - self.miny)
		self.modelwidth, self.modelheight = self.modelsize

		self.xpos = self.maxx
		self.ypos = self.maxy
		self.zoomscale = 1

		#self.connect_after("realize", self._init)
		#self.connect("configure_event", self._reshape)
		self.connect("button_press_event", self._mouseButton)
		self.connect("button_release_event", self._mouseButton)
		#self.connect("motion_notify_event", self._mouseMotion)
		self.connect("scroll_event", self._mouseScroll)

		self.set_events(self.get_events() | gdk.BUTTON_PRESS_MASK | gdk.BUTTON_RELEASE_MASK)#|gdk.POINTER_MOTION_MASK|gdk.POINTER_MOTION_HINT_MASK)

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

		draw(cr)

def draw(cr):
	draw_pads(cr)
	draw_silk(cr)

def draw_silk(cr):
	cr.set_line_cap(cairo.LINE_CAP_ROUND)

	cr.push_group()

	cr.set_source_rgb(0.0, 200/255., 200/255.)
	cr.set_line_width(200); cr.move_to(-200, -300); cr.line_to(-200, 300); cr.stroke()
	cr.set_line_width(80); cr.move_to(400, 300); cr.line_to(600, 300); cr.stroke()
	cr.set_line_width(80); cr.move_to(500, 200); cr.line_to(500, 400); cr.stroke()
	cr.set_line_width(80); cr.move_to(600, 0); cr.line_to(300, 0); cr.stroke()
	cr.set_line_width(80); cr.move_to(300, 0); cr.line_to(300, -400); cr.stroke()
	cr.set_line_width(80); cr.move_to(300, -400); cr.line_to(100, -400); cr.stroke()
	cr.set_line_width(80); cr.move_to(100, -400); cr.line_to(100, 400); cr.stroke()
	cr.set_line_width(80); cr.move_to(100, 400); cr.line_to(300, 400); cr.stroke()
	cr.set_line_width(80); cr.move_to(300, 400); cr.line_to(300, 0); cr.stroke()
	cr.set_line_width(80); cr.move_to(-600, 0); cr.line_to(-300, 0); cr.stroke()
	cr.set_line_width(80); cr.move_to(-300, 0); cr.line_to(-300, -400); cr.stroke()
	cr.set_line_width(80); cr.move_to(-300, -400); cr.line_to(-100, -400); cr.stroke()
	cr.set_line_width(80); cr.move_to(-100, -400); cr.line_to(-100, 400); cr.stroke()
	cr.set_line_width(80); cr.move_to(-100, 400); cr.line_to(-300, 400); cr.stroke()
	cr.set_line_width(80); cr.move_to(-300, 400); cr.line_to(-300, 0); cr.stroke()

	cr.set_line_width(150); cr.arc(0, 0, 1000, 0, 2 * math.pi); cr.stroke()

	cr.pop_group_to_source()
	cr.paint_with_alpha(0.8)

def draw_pads(cr):
	cr.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
	cr.set_source_rgba(160/255., 160/255., 0.0, 0.8)

	cr.rectangle(-1000 - 700/2, -700/2, 700, 700)
	cr.arc(-1000, 0, 400/2, 0, 2 * math.pi)
	cr.fill()

	cr.arc(1000, 0, 700/2, 0, 2 * math.pi)
	cr.arc(1000, 0, 400/2, 0, 2 * math.pi)
	cr.fill()

# GTK mumbo-jumbo to show the widget in a window and quit when it's closed
def run(Widget):
	window = gtk.Window()
	window.connect("delete-event", gtk.main_quit)
	widget = Widget()
	widget.show()
	window.add(widget)
	window.present()
	widget._reshape()
	gtk.main()

if __name__ == "__main__":
	run(CairoGTK)

