#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk

import bip
import goocanvas
import sys
import os


class FITSCanvas(object):

    CONTRAST = 1
    ZOOM = 2
    PAN = 3

    def __init__(self, frame):

        self.dragging = False
        self.lastPos = (0, 0)

        self.tool = FITSCanvas.CONTRAST

        self.frame = frame

        gtk.icon_theme_get_default().append_search_path(
            os.path.abspath(os.path.dirname(__file__)))

        self.window = gtk.ScrolledWindow()
        self.window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.canvas = goocanvas.Canvas()
        self.canvas.set_property("automatic-bounds", True)

        self.builder = gtk.Builder()
        self.builder.add_from_file(
            os.path.join(os.path.dirname(__file__), "canvas.xml"))
        self.builder.connect_signals({"contrast_activate_cb": self.contrast_activate_cb,
                                      "zoom_activate_cb": self.zoom_activate_cb,
                                      "pan_activate_cb": self.pan_activate_cb,
                                      "_98_activate_cb": self._98_activate_cb,
                                      "minmax_activate_cb": self.minmax_activate_cb,
                                      "linear_activate_cb": self.linear_activate_cb,
                                      "log_activate_cb": self.log_activate_cb,
                                      "invert_activate_cb": self.invert_activate_cb,
                                      "reset_contrast_activate_cb": self.reset_contrast_activate_cb})

        w, h = self.frame.get_image().get_width(
        ), self.frame.get_image().get_height()

        self.canvas.set_bounds(0, 0, w, h)
        canvasItem = goocanvas.Image(pixbuf=frame.get_pixbuf(), x=0, y=0)
        self.canvas.get_root_item().add_child(canvasItem)
        self.canvasImage = self.canvas.get_root_item().get_child(0)

        # connect canvas events
        self.canvas.connect("button-press-event", self.button_press_callback)
        self.canvas.connect(
            "button-release-event", self.button_release_callback)
        self.canvas.connect("motion-notify-event", self.motion_notify_callback)

        # create our accelerator maps
        #gtk.accel_map_add_entry("<canvas>/Zoom", ord('z'), 0)

        # connect accelerator
        #accel_group = self.builder.get_object("canvasAcceleratorGroup")
        #accel_group.connect_by_path("<canvas>/Zoom", self.zoom_activate_cb)

        # self.window.get_parent().add_accel_group(accel_group)

        # go!
        self.window.add(self.canvas)
        self.window.show_all()

    def contrast_activate_cb(self, action):
        self.tool = FITSCanvas.CONTRAST
        self.canvas.get_window().set_cursor(gtk.gdk.Cursor(gtk.gdk.ARROW))

    def zoom_activate_cb(self, action):
        self.tool = FITSCanvas.ZOOM
        self.canvas.get_window().set_cursor(gtk.gdk.Cursor(gtk.gdk.PLUS))

    def pan_activate_cb(self, action):
        self.tool = FITSCanvas.PAN
        self.canvas.get_window().set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))

    def _98_activate_cb(self, action):
        image = self.frame.get_image()
        start, end = image.get_histo().get_limits(98.0)
        image.get_scaled().set_min(start)
        image.get_scaled().set_max(end)
        image.get_scaled().update()
        self.frame.update_pixbuf()
        self.canvasImage.set_property("pixbuf", self.frame.get_pixbuf())

    def minmax_activate_cb(self, action):
        image = self.frame.get_image()
        start, end = image.get_stats().get_min(), image.get_stats().get_max()
        image.get_scaled().set_min(start)
        image.get_scaled().set_max(end)
        image.get_scaled().update()
        self.frame.update_pixbuf()
        self.canvasImage.set_property("pixbuf", self.frame.get_pixbuf())

    def linear_activate_cb(self, action):
        image = self.frame.get_image()
        image.get_scaled().set_type(bip.SCALED_IMAGE_SCALE_LINEAR)
        image.get_scaled().update()
        self.frame.update_pixbuf()
        self.canvasImage.set_property("pixbuf", self.frame.get_pixbuf())

    def log_activate_cb(self, action):
        image = self.frame.get_image()
        image.get_scaled().set_type(bip.SCALED_IMAGE_SCALE_LOG)
        image.get_scaled().update()
        self.frame.update_pixbuf()
        self.canvasImage.set_property("pixbuf", self.frame.get_pixbuf())

    def invert_activate_cb(self, action):
        cmap = self.frame.get_colormap()
        cmap.set_invert(not cmap.get_invert())
        cmap.update()
        self.frame.update_pixbuf()
        self.canvasImage.set_property("pixbuf", self.frame.get_pixbuf())

    def reset_contrast_activate_cb(self, action):
        cmap = self.frame.get_colormap()
        cmap.set_bias(0.5)
        cmap.set_contrast(1)
        cmap.update()
        self.frame.update_pixbuf()
        self.canvasImage.set_property("pixbuf", self.frame.get_pixbuf())

    def button_press_callback(self, canvas, event):

        if event.button == 3:
            self.builder.get_object("popup").popup(
                None, None, None, event.button, event.time)

        if event.button == 1:
            self.dragging = True
            self.lastPos = (event.x, event.y)

            if self.tool == FITSCanvas.ZOOM:
                self.zoom(event.state & gtk.gdk.CONTROL_MASK)

    def button_release_callback(self, canvas, event):
        self.dragging = False

    def motion_notify_callback(self, canvas, event):

        if self.dragging:

            delta_x = event.x - self.lastPos[0]
            delta_y = event.y - self.lastPos[1]

            if self.tool == FITSCanvas.CONTRAST:
                if abs(delta_x) >= 2 or abs(delta_y) >= 2:
                    self.changeContrast(event.x, event.y)

            if self.tool == FITSCanvas.PAN:
                self.pan(delta_x, delta_y)

            self.lastPos = (event.x, event.y)

    def changeContrast(self, x, y):
        width = self.window.get_allocation().width
        height = self.window.get_allocation().height

        bias = (x / float(width))
        if bias < 0:
            bias = 0
        if bias > 1:
            bias = 1

        contrast = 10 * (y / float(height))
        if contrast < 0:
            contrast = 0
        if contrast > 10:
            contrast = 10

        cmap = self.frame.get_colormap()
        cmap.set_bias(bias)
        cmap.set_contrast(contrast)
        cmap.update()
        self.frame.update_pixbuf()
        self.canvasImage.set_property("pixbuf", self.frame.get_pixbuf())

    def zoom(self, ctrl=False):
        if ctrl:
            self.canvas.set_scale(self.canvas.get_scale() - 0.25)
        else:
            self.canvas.set_scale(self.canvas.get_scale() + 0.25)

    def pan(self, dx, dy):
        h_adjust = self.window.get_hadjustment()
        v_adjust = self.window.get_vadjustment()

        h_adjust.set_value(h_adjust.get_value() - dx)
        v_adjust.set_value(v_adjust.get_value() - dy)


class FITS(object):

    def __init__(self, filename):
        self.img = bip.Image(filename)

        start, end = self.img.get_histo().get_limits(98.0)
        self.img.get_scaled().set_min(start)
        self.img.get_scaled().set_max(end)
        self.img.get_scaled().update()

        cmap = bip.bip_colormap_get_builtin(bip.COLORMAP_GRAY)
        cmap.set_invert(False)
        cmap.update()

        self.frame = bip.Frame(1, self.img, cmap)
        self.frame.update_pixbuf()

if __name__ == "__main__":

    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.connect("destroy", gtk.main_quit)

    fits = FITS(sys.argv[1])
    canvas = FITSCanvas(fits.frame)

    canvas.window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    window.set_size_request(fits.img.get_width(), fits.img.get_height())
    window.add(canvas.window)
    window.show_all()
    gtk.main()
