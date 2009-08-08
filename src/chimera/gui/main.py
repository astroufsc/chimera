#!/usr/bin/env python
# -*- coding: utf-8 -*-

from chimera.gui.canvas import FITS, FITSCanvas

import sys
import time
import os

try:
    import pygtk
    pygtk.require("2.0")
except:
    raise Exception("No PyGTK+ available!")

try:
    import gtk
    import gtk.glade
    import gobject
    import time
    import threading, thread
except Exception, e:
    print e
    sys.exit(1)

try:
    import glib
except ImportError:
    # Ubuntu 8.04?
    glib = gobject

# DON'T REMOVE THE NEXT LINE!
gtk.gdk.threads_init()

from chimera.core.systemconfig import SystemConfig
from chimera.core.callback import callback
from chimera.core.manager import Manager
from chimera.core.managerlocator   import ManagerLocator, ManagerNotFoundException
from chimera.interfaces.filterwheel import InvalidFilterPositionException
from chimera.interfaces.telescope  import SlewRate
from chimera.core.constants import SYSTEM_CONFIG_DEFAULT_FILENAME
from chimera.core.exceptions import InvalidLocationException, printException
from chimera.util.coord import Coord
from chimera.util.position import Position
from chimera.util.position import Epoch

import subprocess


class CameraController:

    def __init__ (self, main):
        self.main = main
        self.camera = None
        self.wheel = None

    def setCamera(self, camera):
        self.camera = camera        

        @callback(self.main.localManager)
        def exposeBegin(request):
            self.main.cameraView.exposeBegin(request)
            
        @callback(self.main.localManager)
        def exposeComplete(request):
            self.main.cameraView.exposeComplete(request)

        @callback(self.main.localManager)
        def readoutBegin(request):
            self.main.cameraView.readoutBegin(request)
                
        @callback(self.main.localManager)
        def readoutComplete(image):
            self.main.cameraView.readoutComplete(image)
            
        @callback(self.main.localManager)
        def abortComplete():
            self.main.cameraView.abort()
            
        self.camera.exposeBegin     += exposeBegin
        self.camera.exposeComplete  += exposeComplete
        self.camera.abortComplete   += abortComplete
        self.camera.readoutBegin    += readoutBegin
        self.camera.readoutComplete += readoutComplete

    def getCamera(self):
        # transfer to current thread and return (a hacky way to reuse Proxies)
        self.camera._transferThread()
        return self.camera

    def setFilterWheel(self, wheel):
        self.wheel = wheel

    def getWheel(self):
        # transfer to current thread and return (a hacky way to reuse Proxies)
        self.wheel._transferThread()
        return self.wheel

    def expose(self):

        camera = self.getCamera()
        
        durationSpin = self.main.builder.get_object("durationSpin")
        duration = durationSpin.get_value()
        
        framesSpin = self.main.builder.get_object("framesSpin")
        frames = framesSpin.get_value()
        
        shutterOpen = self.main.builder.get_object("shutterOpen")

        if(shutterOpen.get_active()):
          shutterState = "OPEN"
        else: 
          shutterState = "CLOSE"

        filters = self.main.builder.get_object("filtersBox").get_children()[1].get_children()
        current = None
        for f in filters:
            if f.get_active(): current = f

        filterName = current.get_label()

        self.main.cameraView.begin(duration, frames)

        if self.getWheel().getFilter() != filterName:
            self.main.cameraView.beginFilterChange(filterName)        
            self.getWheel().setFilter(filterName)
            self.main.cameraView.endFilterChange(filterName)                

        try:
            camera.expose({"exptime": duration,
                           "frames": frames,
                           "shutter": shutterState})
        except Exception, e:
            printException(e)

        finally:
            self.main.cameraView.end()
    
    def abortExposure (self):
        self.getCamera().abortExposure()
        self.main.cameraView.abort()

class CameraView:

    def __init__ (self, main):
        self.main = main
        self.exposureStatusbar = self.main.builder.get_object("exposureStatusbar")
        self.exposureLabel = self.main.builder.get_object("exposureLabel")
        self.exposureProgress = self.main.builder.get_object("exposureProgress")

        self.exposureLabel.hide()
        self.exposureProgress.hide()
        self.exposureProgress.set_pulse_step(0.1)

        self.frames = 0
        self.exptime = 0
        self.currentFrame = 0
        
        self.exposeTimer = None
        self.readoutTimer = None
        self.filterTimer = None
        
    def begin(self, exptime, frames):
        self.frames = frames
        self.exptime = exptime
        self.currentFrame = 0

        def ui():
            
            self.main.builder.get_object("abortExposureButton").set_sensitive(True)
            self.main.builder.get_object("exposeButton").set_sensitive(False)
            
            self.exposureLabel.set_label("<b>%-2d/%-2d</b>" % (self.currentFrame, self.frames))
            self.exposureProgress.set_fraction(0.0)
            self.exposureProgress.set_text("starting ...")
            
            self.exposureLabel.show()
            self.exposureProgress.show()

        glib.idle_add(ui)
        
    def exposeBegin(self, imageRequest):

        startTime = time.time()
        timeout = startTime + self.exptime
        
        self.currentFrame += 1

        def ui():
            
            self.exposureLabel.set_label("<b>%-2d/%-2d</b>" % (self.currentFrame, self.frames))
            self.exposureProgress.set_fraction(0.0)

            def exposeTimer(startTime, timeout):
                now = time.time()
                if now >= timeout: return False
            
                counter = now - startTime
                self.exposureProgress.set_fraction(counter/self.exptime)
                self.exposureProgress.set_text("%.2f" % (self.exptime - counter))
                return True

            self.exposeTimer = glib.timeout_add(100, exposeTimer, startTime, timeout)

        glib.idle_add(ui)

    def exposeComplete(self, imageRequest):

        def ui():
            self.exposureProgress.set_fraction(1.0)
            self.exposureProgress.set_text("exposure complete ...")

            if self.exposeTimer:
                glib.source_remove(self.exposeTimer)
                self.exposeTimer = 0
                
        glib.idle_add(ui)

    def readoutBegin(self, imageRequest):

        def ui():
            
            self.exposureProgress.set_text("reading out and saving ...")
        
            def readoutTimer():
                self.exposureProgress.pulse()
                return True
        
            self.readoutTimer = glib.timeout_add(100, readoutTimer)

        glib.idle_add(ui)
        
    def readoutComplete(self, image):
        
        if self.readoutTimer:
            glib.source_remove(self.readoutTimer)
            self.readoutTimer = 0

        def ui():
            self.exposureProgress.set_fraction(1.0)
            self.exposureProgress.set_text("readout and save complete ...")
            self.main.imageViewer.newImage(image)
        glib.idle_add(ui)

    def end(self):

        def ui():
            self.exposureLabel.hide()
            self.exposureProgress.hide()

            self.main.builder.get_object("abortExposureButton").set_sensitive(False)
            self.main.builder.get_object("exposeButton").set_sensitive(True)
        glib.idle_add(ui)

    def abort(self):

        def ui():
            self.exposureProgress.set_text("aborted!")
            self.main.builder.get_object("abortExposureButton").set_sensitive(False)
            self.main.builder.get_object("exposeButton").set_sensitive(True)

            def abortTimer():
                self.exposureLabel.hide()
                self.exposureProgress.hide()
                return False
            glib.timeout_add(2000, abortTimer)
            
        glib.idle_add(ui)

    def beginFilterChange(self, filterName):

        def filterTimer():
            self.exposureProgress.pulse()
            return True
        self.filterTimer = glib.timeout_add(50, filterTimer)

        def ui():
            self.exposureProgress.set_text("switching to filter %s ..." % filterName)
        
        glib.idle_add(ui)

    def endFilterChange(self, filterName):
        
        if self.filterTimer:
            glib.source_remove(self.filterTimer)
            self.filterTimer = 0

        def ui():
            self.exposureProgress.set_fraction(1.0)
            self.exposureProgress.set_text("filter switch complete!")
        glib.idle_add(ui)


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
    
        
class ImageViewer:
    
    def __init__(self, main):
        self.main = main
        
        self.notebook = self.main.builder.get_object("imagesNotebook")
        self.notebook.append_page(gtk.Label("No images"))

    def newImage(self, image):
        fits = FITS(image.filename())
        canvas = FITSCanvas(fits.frame)
        tab_num = self.notebook.append_page(canvas.window, gtk.Label(os.path.basename(image.filename())))
        self.notebook.set_current_page(tab_num)

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

