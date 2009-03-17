#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import gtk.glade
except:
    sys.exit(1)

class ChimeraGUI:

    def __init__(self):

        self.tree = gtk.glade.XML("chimera.glade", "mainWindow")
        self.tree.signal_autoconnect({})

        win = self.tree.get_widget("mainWindow")
        win.show_all();

if __name__ == "__main__":
    win = ChimeraGUI()
    gtk.main()

