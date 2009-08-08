from chimera.util.position import Position, Epoch
from chimera.util.coord import Coord
from chimera.core.callback import callback

import gtk
import glib

class TelescopeController:
    def __init__ (self, main):
        self.telescope = None
        self.main = main
    
    def setTelescope(self, telescope):
        self.telescope = telescope
        
        self.main.telescopeView.controllerRunning()
        
        
    def getTelescope(self):
        # transfer to current thread and return (a hacky way to reuse Proxies)
        self.telescope._transferThread()
        return self.telescope
    
    def slew(self):
        raHour = self.main.telescopeView.raHourSpin.get_value()
        raMinute = self.main.telescopeView.raMinuteSpin.get_value()
        raSec = self.main.telescopeView.raSecSpin.get_value()
        
        decDegree = self.main.telescopeView.decDegreeSpin.get_value()
        decMinute = self.main.telescopeView.decMinuteSpin.get_value()
        decSec = self.main.telescopeView.decSecSpin.get_value()
        
        ra = "%2d:%2d:%2d" %(raHour, raMinute, raSec)
        dec = "%2d:%2d:%2d" %(decDegree, decMinute, decSec)
        
        target = Position.fromRaDec(ra, dec, equinox=Epoch.J2000)
        
        self.main.telescopeView.slewBeginUi()
        
        @callback(self.main.localManager)
        def slewBegin(target):
            self.main.telescopeView.slewBegin(target)
        
        @callback(self.main.localManager)
        def slewComplete(target):
            self.main.telescopeView.slewComplete(target)
        
        @callback(self.main.localManager)
        def abortComplete(target):
            self.main.telescopeView.abortComplete(target)
        
        self.telescope.slewComplete += slewBegin
        self.telescope.slewComplete += slewComplete
        self.telescope.abortComplete += abortComplete
        
        self.telescope.slewToRaDec(target)
        
        self.telescope.slewComplete -= slewBegin
        self.telescope.slewComplete -= slewComplete
        self.telescope.abortComplete -= abortComplete

        #self.main.telescopeView.slewComplete(target)
        
    def moveEast(self):
        offset = 5
        offset = self._validateOffset(offset)
        
        self.telescope.moveEast(offset)
        
    def moveWest(self):
        offset = 5
        offset = self._validateOffset(offset)
        
        self.telescope.moveWest(offset.AS)
    
    def moveNorth(self):
        offset = 5
        offset = self._validateOffset(offset)
        
        self.telescope.moveNorth(offset.AS)
    
    def moveSouth(self):
        offset = 5
        offset = self._validateOffset(offset)
        
        self.telescope.moveSouth(offset.AS)
    
    def toggleTracking(self):
        if(self.isTracking()):
            self.getTelescope().stopTracking()
            self.main.telescopeView.updateTrackingStatus()
        else:
            self.getTelescope().startTracking()
            self.main.telescopeView.updateTrackingStatus()
            
    def getCurrentRaDec(self):
        telescope = self.getTelescope()
        return telescope.getPositionRaDec()
    
    def getCurrentAltAz(self):
        telescope = self.getTelescope()
        return telescope.getPositionAltAz()
    
    def isTracking(self):
        telescope = self.getTelescope()
        return telescope.isTracking()
    
    def _validateOffset(self, value):
        try:
            offset = Coord.fromAS(int(value))
            print("Hey")
        except ValueError:
            offset = Coord.fromDMS(value)
        
        return offset

class TelescopeView:
    def __init__ (self, main):
        self.main = main
        
        self.raHourSpin = self.main.builder.get_object("raHourSpin")
        self.raMinuteSpin = self.main.builder.get_object("raMinuteSpin")
        self.raSecSpin = self.main.builder.get_object("raSecSpin")
        
        self.decDegreeSpin = self.main.builder.get_object("decDegreeSpin")
        self.decMinuteSpin = self.main.builder.get_object("decMinuteSpin")
        self.decSecSpin = self.main.builder.get_object("decSecSpin")
        
        
        self.epochCombo = self.main.builder.get_object("epochCombo")
        listStore = gtk.ListStore(str)
        listStore.insert(0,["J2000"])
        listStore.insert(1,["B1950"])
        listStore.insert(2, ["Now"])
        
        self.epochCombo.set_model(listStore)
        self.epochCombo.show_all()
        
        
        self.raDecLabel = self.main.builder.get_object("raDecLabel")
        self.altAzLabel = self.main.builder.get_object("altAzLabel")
        
    def updateStatusView(self):
          raDec = self.main.telescopeController.getCurrentRaDec()
          altAz = self.main.telescopeController.getCurrentAltAz()
                
          text = "%s" %raDec
          self.raDecLabel.set_text(text)
          text = "%s" %altAz
          self.altAzLabel.set_text(text)
      
    def controllerRunning(self):
        self.updateTrackingStatus()
        glib.idle_add(self.updateStatusView)
    
    def updateTrackingStatus(self):
        if(self.main.telescopeController.isTracking()):
            status = "On"
        else:
            status = "Off"
        def ui():
            self.main.builder.get_object("trackingLabel").set_text(status)
        glib.idle_add(ui)
        
    def slewBeginUi(self):
        def ui():
            self.raDecLabel.set_text("Slewing...")
            self.altAzLabel.set_text("Slewing...")
            
            self.main.builder.get_object("slewButton").set_sensitive(False)
            
            telescopeProgress = self.main.builder.get_object("telescopeProgress")
            telescopeProgress.show()
            
            def telescopeTimer():
                self.main.builder.get_object("telescopeProgress").pulse()
                return True
            self.telescopeTimer = glib.timeout_add(75, telescopeTimer)
            
        glib.idle_add(ui)
    
    def slewBegin(self, target = None):
        def ui():
            self.raDecLabel.set_text("Slewing...")
            self.altAzLabel.set_text("Slewing...")
        glib.idle_add(ui)
    
    def slewComplete(self, target = None):
        def ui():
            
            raDec = self.main.telescopeController.getCurrentRaDec()
            altAz = self.main.telescopeController.getCurrentAltAz()
            self.raDecLabel.set_text("%s" % raDec)
            self.altAzLabel.set_text("%s" % altAz)
            
            telescopeProgress = self.main.builder.get_object("telescopeProgress")
            telescopeProgress.hide()
            
            if self.telescopeTimer:
                glib.source_remove(self.telescopeTimer)
                self.telescopeTimer = 0
            
            self.main.builder.get_object("slewButton").set_sensitive(True)
            
        glib.idle_add(ui)
    
    def abortComplete(self, target = None):
        def ui():
            pass
        glib.idle_add(ui)
    
        
