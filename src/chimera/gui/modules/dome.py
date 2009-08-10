from chimera.core.callback import callback
from chimera.core.exceptions import printException

from chimera.gui.module import ChimeraGUIModule
from chimera.interfaces.dome import Mode

import gtk
import glib
import gdl

import os
import threading

class DomeController:

    def __init__ (self, module):
        self.module = module
        self.dome = None

    def setDome(self, dome):
        self.dome = dome

        @callback(self.module.manager)
        def on_slit_close(az):
            self.module.view.updateSlitStatus()
            
        @callback(self.module.manager)
        def on_slit_open(az):
            self.module.view.updateSlitStatus()

        @callback(self.module.manager)
        def on_slew_begin(az):
            self.module.view.slewBegin(az)
            
        @callback(self.module.manager)
        def on_slew_complete(az):
            self.module.view.slewComplete(az)

        self.dome.slitOpened   += on_slit_open
        self.dome.slitClosed   += on_slit_close
        self.dome.slewBegin    += on_slew_begin
        self.dome.slewComplete += on_slew_complete

    def getDome(self):
        # transfer to current thread and return (a hacky way to reuse Proxies)
        self.dome._transferThread()
        return self.dome

    def openSlit(self):
        self.module.view.slitChangeBegin()
        self.dome.openSlit()

    def closeSlit(self):
        self.module.view.slitChangeBegin()
        self.dome.closeSlit()

    def isSlitOpen(self):
        return self.dome.isSlitOpen()

    def getAz(self):
        return self.dome.getAz()

    def slew(self):
        az = self.module.view.azEntry.get_text()
        try:
            self.dome.slewToAz(az)
        except Exception, e:
            printException(e)

    def isTracking(self):
        if self.dome.getMode() == Mode.Track:
            return True
        return False

    def isSlewing(self):
        return self.dome.isSlewing()

    def toggleTracking (self):

        if self.dome.getMode() == Mode.Stand:
            self.dome.track()
        else:
            self.dome.stand()

        self.module.view.updateTrackingStatus()

class DomeView:

    def __init__ (self, module):
        self.module = module

        self.positionLabel = self.module.builder.get_object("positionLabel")
        self.openButton = self.module.builder.get_object("openButton")
        self.closeButton = self.module.builder.get_object("closeButton")
        self.azEntry = self.module.builder.get_object("azEntry")
        self.slewButton = self.module.builder.get_object("slewButton")
        self.trackingCheckbox = self.module.builder.get_object("trackingCheckbox")

        self.updateTimer = None

    def updateSlitStatus (self):
        def ui():
            if self.module.controller.isSlitOpen():
                self.openButton.set_sensitive(False)
                self.closeButton.set_sensitive(True)            
            else:
                self.openButton.set_sensitive(True)
                self.closeButton.set_sensitive(False)
                
        glib.idle_add(ui)

    def startUpdateTimer (self):
        self.updateTimer = glib.timeout_add(2000, self.updateDomePosition)

    def pauseUpdateTimer (self):
        if self.updateTimer:
            glib.source_remove(self.updateTimer)

    def updateDomePosition (self):
        self.positionLabel.set_text(str(self.module.controller.getAz()))
        return True

    def slewBegin (self, az):
        def ui():
            self.pauseUpdateTimer()
            self.slewButton.set_sensitive(False)
        glib.idle_add(ui)

    def slewComplete (self, az):
        def ui():
            self.startUpdateTimer()
            self.slewButton.set_sensitive(True)
            self.updateTrackingStatus()
        glib.idle_add(ui)

    def slitChangeBegin (self):
        def ui():
            self.openButton.set_sensitive(False)
            self.closeButton.set_sensitive(False)
        glib.idle_add(ui)

    def updateTrackingStatus (self):
        if self.module.controller.isTracking():
            self.trackingCheckbox.set_active(True)
            self.slewButton.set_sensitive(False)
            self.azEntry.set_sensitive(False)
        else:
            self.trackingCheckbox.set_active(False)
            self.slewButton.set_sensitive(True)
            self.azEntry.set_sensitive(True)

class DomeGUIModule(ChimeraGUIModule):

    module_controls = {"dome": "Dome"}

    def __init__ (self, manager):
        ChimeraGUIModule.__init__(self, manager)

        self.view = None
        self.controller = None

    def setupGUI (self, objects):

        dome = objects.get("dome", None)

        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(os.path.dirname(__file__), "dome.xml"))

        self.view = DomeView(self)
        self.controller = DomeController(self)
        self.controller.setDome(dome)

        self.view.updateSlitStatus()
        self.view.startUpdateTimer()
        self.view.updateTrackingStatus()

        win = self.builder.get_object("window")
        gui = self.builder.get_object("gui")
        win.remove(gui)
        
        return [("Dome", gui, gdl.DOCK_CENTER)]
        
    def setupEvents (self):

        def on_close_action(action):
            threading.Thread(target=self.controller.closeSlit).start()
    
        def on_open_action(action):
            threading.Thread(target=self.controller.openSlit).start()

        def on_slew_action(action):
            threading.Thread(target=self.controller.slew).start()

        def on_track_action(action):
            threading.Thread(target=self.controller.toggleTracking).start()            
    
        self.builder.connect_signals({"on_close_action": on_close_action,
                                      "on_open_action" : on_open_action,
                                      "on_slew_action" : on_slew_action,
                                      "on_track_action": on_track_action})
