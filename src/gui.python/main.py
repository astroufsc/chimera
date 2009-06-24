#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import os

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import gtk.glade
    import gobject
    import glib
    import time
    import threading, thread
    from canvas import FITS, FITSCanvas
except:
    sys.exit(1)

# DON'T REMOVE THE NEXT LINE!
gtk.gdk.threads_init()

from chimera.core.systemconfig import SystemConfig
from chimera.core.callback import callback
from chimera.core.manager import Manager
from chimera.core.managerlocator   import ManagerLocator, ManagerNotFoundException
from chimera.interfaces.filterwheel import InvalidFilterPositionException
from chimera.core.constants import SYSTEM_CONFIG_DEFAULT_FILENAME
from chimera.core.exceptions import InvalidLocationException, printException

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
        
        shutterButton = self.main.builder.get_object("shutterButton")
        if(shutterButton.get_active()):
          shutterState = "CLOSE"
        else: 
          shutterState = "OPEN"

        filters = self.main.builder.get_object("filtersBox").get_children()[1].get_children()
        current = None
        for f in filters:
            if f.get_active(): current = f

        filterName = current.get_label()

        self.main.cameraView.begin(duration, frames)

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

        print time.time()
        
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

        def ui():
            self.exposureProgress.set_text("switching to filter %s ..." % filterName)
        
            def filterTimer():
                self.exposureProgress.pulse()
                return True
            self.filterTimer = glib.timeout_add(50, filterTimer)

        glib.idle_add(ui)

    def endFilterChange(self, filterName):
        
        if self.filterTimer:
            glib.source_remove(self.filterTimer)
            self.filterTimer = 0

        def ui():
            self.exposureProgress.set_fraction(1.0)
            self.exposureProgress.set_text("filter switch complete!")
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
        self.builder.add_from_file("chimera.xml")
             
        def toggle_shutter_button(widget):
            if widget.get_label() == "open":
                widget.set_label("closed")
            else:
                widget.set_label("open")

        self.builder.connect_signals({"on_shutter_toggle": toggle_shutter_button,
                                      "window_destroy": gtk.main_quit,
                                      "camera_expose_action": self.camera_expose_action,
                                      "camera_abort_action" : self.camera_abort_action})
                
        self.mainWindow = self.builder.get_object("mainWindow")

        self.cameraView = CameraView(self)
        self.cameraController = CameraController(self)
        self.imageViewer = ImageViewer(self)

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

        self.cameraController.setCamera(camera)
        self.cameraController.setFilterWheel(wheel)

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

        self.builder.get_object("abortExposureButton").set_sensitive(False)
        self.mainWindow.set_default_size(640, 480)
        self.mainWindow.show()

    def camera_expose_action(self, action):
        print time.time()
        self.builder.get_object("abortExposureButton").set_sensitive(True)
        self.builder.get_object("exposeButton").set_sensitive(False)
        threading.Thread(target=self.cameraController.expose).start()

    def camera_abort_action(self, action):
        threading.Thread(target=self.cameraController.abortExposure).start()
    
if __name__ == "__main__":
    ChimeraGUI()
    gtk.main()

