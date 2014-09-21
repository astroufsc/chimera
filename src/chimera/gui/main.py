#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import glob
import imp
import threading
import logging

try:
    import pygtk
    pygtk.require("2.0")
except:
    raise Exception("No PyGTK+ available!")

try:
    import gtk
    import gdl
except Exception, e:
    print e
    sys.exit(1)

# DON'T REMOVE THE NEXT LINE!
gtk.gdk.threads_init()

from chimera.core.systemconfig import SystemConfig
from chimera.core.manager import Manager
from chimera.core.managerlocator import ManagerLocator
from chimera.core.constants import SYSTEM_CONFIG_DEFAULT_FILENAME


class ChimeraGUI:

    def __init__(self):

        self.setupGUI()
        self.setupChimera()
        self.setupViews()

    def setupGUI(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file(
            os.path.join(os.path.dirname(__file__), "chimera.xml"))

        self.mainWindow = self.builder.get_object("mainWindow")
        self.builder.connect_signals({"window_destroy": self.chimera_quit,
                                      "chimera_connect_handler": self.chimera_connect_handler,
                                      "chimera_quit_handler": self.chimera_quit})

        self.dock = gdl.Dock()
        self.dock_layout = gdl.DockLayout()

        if os.path.exists("chimera_gui_layout.xml"):
            self.dock_layout.load_from_file("chimera_gui_layout.xml")
            self.dock_layout.load_layout("_-default__")

        self.builder.get_object("main_area").pack_end(self.dock)

        self.mainWindow.set_default_size(640, 480)
        self.mainWindow.show_all()

    def chimera_quit(self, *arga, **kwargs):
        # self.dock_layout.save_to_file("chimera_gui_layout.xml")
        gtk.main_quit()

    def chimera_connect_handler(self, action):
        threading.Thread(target=self.showConnectDialog).start()

    def showConnectDialog(self):
        dialog = self.builder.get_object("chimera_connect_dialog")
        response = dialog.run()
        dialog.hide()
        dialog.destroy()

    def setupChimera(self):
        try:
            self.sysconfig = SystemConfig.fromFile(
                SYSTEM_CONFIG_DEFAULT_FILENAME)
        except IOError, e:
            logging.exception(e)
            logging.error(
                "There was a problem reading your configuration file. (%s)" % e)
            return False

        self.localManager = Manager(
            host=self.sysconfig.chimera["host"], port=9000)
        self.manager = ManagerLocator.locate(
            self.sysconfig.chimera["host"], self.sysconfig.chimera["port"])

    def getFirstProxy(self, type):
        objs = self.manager.getResourcesByClass(type)
        if objs:
            return self.manager.getProxy(objs[0])
        else:
            raise Exception("ERRO")

    def setupViews(self):

        controls = {}

        for module in self.getAvailableModules():
            controls[module] = module.module_controls

        views = []

        for control, objs in controls.items():

            proxies = {}

            for id, name in objs.items():
                try:
                    proxies[id] = self.getFirstProxy(name)
                except Exception:
                    print "No %s available to %s view." % (name, control)

            if any(proxies):
                view = {"instance": control(self.localManager)}
                view["widgets"] = view["instance"].setupGUI(proxies)
                views.append(view)

        for view in views:

            for name, widget, position in view["widgets"]:

                item = gdl.DockItem(name, name, gdl.DOCK_ITEM_BEH_CANT_ICONIFY)
                item.add(widget)
                item.show_all()
                self.dock.add_item(item, gdl.DOCK_CENTER)

            view["instance"].setupEvents()

    def getChimeraModules(self):
        return self.manager.getResources()

    def getAvailableModules(self):

        module_names = glob.glob(
            "%s/[a-zA-Z]*.py" % os.path.join(os.path.dirname(__file__),
                                             "modules"))

        modules = []

        for module_name in module_names:
            mod = imp.load_source("mod", module_name)
            for name in dir(mod):
                if "GUIModule" in name and name != "ChimeraGUIModule":
                    modules.append(getattr(mod, name))

        return modules

    def run(self, args=[]):
        self.mainWindow.show_all()
        gtk.main()

if __name__ == "__main__":
    ChimeraGUI()
    gtk.main()
