import os

import gtk
import gdl

dock = gdl.Dock()
dock_layout = gdl.DockLayout(dock)

dockbar = gdl.DockBar(dock)

def get_item(module):
    builder = gtk.Builder()
    builder.add_from_file(os.path.join(os.path.dirname(__file__), "modules/%s.xml" % module))
                 
    item = gdl.DockItem(module, module.capitalize(), gtk.STOCK_EXECUTE, gdl.DOCK_ITEM_BEH_NORMAL)
    window = builder.get_object("window")
    gui = builder.get_object("gui")
    window.remove(gui)
    item.add(gui)
    return item

cam = get_item("camera")
tel = get_item("telescope")

dock.add_item(cam, gdl.DOCK_TOP)
dock.add_item(tel, gdl.DOCK_TOP)

cam.show()
tel.show()
dock.show()

mainWindow = gtk.Window(gtk.WINDOW_TOPLEVEL)
mainWindow.add(dock)
mainWindow.show_all()

gtk.main()
