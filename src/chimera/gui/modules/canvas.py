
import pygtk
pygtk.require('2.0')
import gtk

import bip
import goocanvas
import sys

class FITSCanvas(object):

    def __init__(self, frame):
        
        self.window = gtk.ScrolledWindow()
        self.window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.canvas = goocanvas.Canvas()
        self.canvas.set_property("automatic-bounds", True)       

        self.frame = frame

        w, h = self.frame.get_image().get_width(), self.frame.get_image().get_height()

        self.canvas.set_bounds(0, 0, w, h)
        canvasItem = goocanvas.Image(pixbuf=frame.get_pixbuf(), x=0, y=0)
        self.canvas.get_root_item().add_child(canvasItem)

        self.window.add(self.canvas)
        self.window.show_all()

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

    fits = FITS(sys.argv[1])
    canvas = FITSCanvas(fits.frame)

    canvas.window.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
    window.set_size_request(fits.img.get_width(), fits.img.get_height())
    window.add(canvas.window)
    window.show_all()
    gtk.main()
    
