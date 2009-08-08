#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import threading

try:
    import pygtk
    pygtk.require("2.0")
except:
    raise Exception("No PyGTK+ available!")

try:
    import gtk
except Exception, e:
    print e
    sys.exit(1)

# DON'T REMOVE THE NEXT LINE!
gtk.gdk.threads_init()

from chimera.core.systemconfig import SystemConfig
from chimera.core.manager import Manager
from chimera.core.managerlocator   import ManagerLocator
from chimera.core.constants import SYSTEM_CONFIG_DEFAULT_FILENAME
from chimera.core.exceptions import InvalidLocationException

from chimera.gui.modules.telescope import TelescopeView, TelescopeController
from chimera.gui.modules.camera import CameraView, CameraController, ImageViewer

class ChimeraGUI:
    
    def __init__(self):
        
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(os.path.dirname(__file__), "chimera.xml"))
             
        def toggle_shutter_button(widget):
            if widget.get_label() == "open":
                widget.set_label("closed")
            else:
                widget.set_label("open")
        
        self.builder.connect_signals({"on_shutter_toggle": toggle_shutter_button,
                                      "window_destroy": gtk.main_quit,
                                      "camera_expose_action": self.camera_expose_action,
                                      "camera_abort_action" : self.camera_abort_action,
                                      "telescope_slew_action": self.telescope_slew_action,
                                      "telescope_move_east_action": self.telescope_move_east_action,
                                      "telescope_move_west_action": self.telescope_move_west_action,
                                      "telescope_move_north_action": self.telescope_move_north_action,
                                      "telescope_move_south_action": self.telescope_move_south_action,
                                      "telescope_tracking_action": self.telescope_tracking_action})
                
        self.mainWindow = self.builder.get_object("mainWindow")
        
        self.cameraView = CameraView(self)
        self.cameraController = CameraController(self)
        self.imageViewer = ImageViewer(self)
        
        self.telescopeView = TelescopeView(self)
        self.telescopeController = TelescopeController(self)
        self.telescopeInit = False
        
        try:
            self.sysconfig = SystemConfig.fromFile(SYSTEM_CONFIG_DEFAULT_FILENAME)
        except (InvalidLocationException, IOError), e:
            log.exception(e)
            log.error("There was a problem reading your configuration file. (%s)" % e)
            sys.exit(1)
        
        self.localManager = Manager(host=self.sysconfig.chimera["host"], port=9000)
        
        def getFirst(type):
            objs = self.manager.getResourcesByClass(type)
            if objs:
                return self.manager.getProxy(objs[0])
            else:
                raise Exception("ERRO")
        
        self.manager = ManagerLocator.locate(self.sysconfig.chimera["host"], self.sysconfig.chimera["port"])
        camera = getFirst("Camera")
        wheel = getFirst("FilterWheel")
        telescope = getFirst("Telescope")
        
        self.cameraController.setCamera(camera)
        self.cameraController.setFilterWheel(wheel)
        self.telescopeController.setTelescope(telescope)
        
        # Query telescope tracking status and adjust UI accordingly
        self.telescopeView.updateTrackingStatus()
        if(telescope.isTracking()):
            self.builder.get_object("trackingButton").set_active(True)
        else:
            self.builder.get_object("trackingButton").set_active(False)
        
        self.telescopeInit = True
        
        # some UI tweaks
        self.builder.get_object("durationSpin").set_value(1)
        self.builder.get_object("framesSpin").set_value(1)        
        
        # create filter box
        # ...
        filters = wheel.getFilters()
        hbox = gtk.HBox()
        first = gtk.RadioButton(None, filters[0])
        hbox.pack_start(first)
        for filter in filters[1:]:
            radio = gtk.RadioButton(first, filter)
            hbox.pack_start(radio)
        hbox.show_all()
        
        self.builder.get_object("filtersBox").pack_start(hbox)
        
        #Slew Rate box
        rates = ["Max", "Guide", "Center", "Find"]
        hbox = gtk.HBox()
        first = gtk.RadioButton(None, "Max")
        hbox.pack_start(first)
        for rate in rates[1:]:
            radio = gtk.RadioButton(first, rate)
            hbox.pack_start(radio)
        hbox.show_all()
        self.builder.get_object("slewRateBox").pack_start(hbox)
        
        self.builder.get_object("abortExposureButton").set_sensitive(False)
        self.mainWindow.set_default_size(640, 480)
        self.mainWindow.show()
    
    def camera_expose_action(self, action):
        self.builder.get_object("abortExposureButton").set_sensitive(True)
        self.builder.get_object("exposeButton").set_sensitive(False)
        threading.Thread(target=self.cameraController.expose).start()
    
    def camera_abort_action(self, action):
        threading.Thread(target=self.cameraController.abortExposure).start()
    
    def telescope_slew_action(self, action):
        threading.Thread(target=self.telescopeController.slew).start()
        
    def telescope_move_east_action(self, action):
        threading.Thread(target=self.telescopeController.moveEast).start()
        
    def telescope_move_west_action(self, action):
        threading.Thread(target=self.telescopeController.moveWest).start()
        
    def telescope_move_north_action(self, action):
        threading.Thread(target=self.telescopeController.moveNorth).start()
        
    def telescope_move_south_action(self, action):
        threading.Thread(target=self.telescopeController.moveSouth).start()
        
    def telescope_tracking_action(self, action):
        if(self.telescopeInit):
            threading.Thread(target=self.telescopeController.toggleTracking).start()

    def run(self, args=[]):
        gtk.main()
            
if __name__ == "__main__":
    ChimeraGUI()
    gtk.main()

