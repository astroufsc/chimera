from chimera.core.callback import callback
from chimera.core.exceptions import printException

from chimera.gui.modules.canvas import FITS, FITSCanvas
from chimera.gui.module import ChimeraGUIModule

from chimera.interfaces.camera import CameraStatus
from chimera.util.image import Image

import gtk
import glib
import gdl

import time
import urllib
import os
import threading
import copy

class ImageViewer:
    
    def __init__(self, main):
        self.main = main
        
        self.notebook = self.main.builder.get_object("imagesNotebook")
        self.notebook.append_page(gtk.Label("No images"))
        self.first_image = True

    def newImage(self, image):
        fits = FITS(image.filename())
        canvas = FITSCanvas(fits.frame)

        if self.first_image:
            self.notebook.remove_page(0)
            self.first_image = False            

        tab_num = self.notebook.append_page(canvas.window, gtk.Label(os.path.basename(image.filename())))
            
        self.notebook.set_current_page(tab_num)


class CameraController:

    def __init__ (self, module):
        self.module = module
        self.camera = None
        self.wheel = None

    def setCamera(self, camera):
        self.camera = camera        

        @callback(self.module.manager)
        def exposeBegin(request):
            self.module.view.exposeBegin(request)
            
        @callback(self.module.manager)
        def exposeComplete(request, status):
            if status == CameraStatus.OK:           
                self.module.view.exposeComplete(request)
            else:
                self.module.view.abort()

        @callback(self.module.manager)
        def readoutBegin(request):
            self.module.view.readoutBegin(request)
                
        @callback(self.module.manager)
        def readoutComplete(image, status):
            if status == CameraStatus.OK:
                self.module.view.readoutComplete(image)
            else:
                self.module.view.abort()
                                    
        self.camera.exposeBegin     += exposeBegin
        self.camera.exposeComplete  += exposeComplete
        self.camera.readoutBegin    += readoutBegin
        self.camera.readoutComplete += readoutComplete

    def getCamera(self):
        # create a copy of Proxy to make sure multiple threads don't reuse it
        return copy.copy(self.camera)

    def setFilterWheel(self, wheel):
        self.wheel = wheel

    def getWheel(self):
        # transfer to current thread and return (a hacky way to reuse Proxies)
        self.wheel._transferThread()
        return self.wheel

    def expose(self):

        camera = self.getCamera()
        
        durationSpin = self.module.builder.get_object("durationSpin")
        duration = durationSpin.get_value()
        
        framesSpin = self.module.builder.get_object("framesSpin")
        frames = framesSpin.get_value()
        
        shutterOpen = self.module.builder.get_object("shutterOpen")

        if(shutterOpen.get_active()):
          shutterState = "OPEN"
        else: 
          shutterState = "CLOSE"

        filters = self.module.builder.get_object("filtersBox").get_children()[1].get_children()
        current = None
        for f in filters:
            if f.get_active(): current = f

        filterName = current.get_label()

        self.module.view.begin(duration, frames)

        if self.getWheel().getFilter() != filterName:
            self.module.view.beginFilterChange(filterName)        
            self.getWheel().setFilter(filterName)
            self.module.view.endFilterChange(filterName)                

        try:
            camera.expose({"exptime": duration,
                           "frames": frames,
                           "shutter": shutterState})
        except Exception, e:
            printException(e)

        finally:
            self.module.view.end()
    
    def abortExposure (self):
        self.getCamera().abortExposure()
        self.module.view.abort()

class CameraView:

    def __init__ (self, module):
        self.module = module
        self.exposureStatusbar = self.module.builder.get_object("exposureStatusbar")
        self.exposureLabel = self.module.builder.get_object("exposureLabel")
        self.exposureProgress = self.module.builder.get_object("exposureProgress")

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
            
            self.module.builder.get_object("abortExposureButton").set_sensitive(True)
            self.module.builder.get_object("exposeButton").set_sensitive(False)
            
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
            url = image.http()
            imageFileName = urllib.urlretrieve(url, filename=os.path.basename(image.filename()))[0]
            imageFile = Image.fromFile(imageFileName)
            self.module.imageViewer.newImage(imageFile)
        glib.idle_add(ui)

    def end(self):

        def ui():
            self.exposureLabel.hide()
            self.exposureProgress.hide()

            self.module.builder.get_object("abortExposureButton").set_sensitive(False)
            self.module.builder.get_object("exposeButton").set_sensitive(True)
        glib.idle_add(ui)

    def abort(self):

        def ui():
            self.exposureProgress.set_text("aborted!")
            self.module.builder.get_object("abortExposureButton").set_sensitive(False)
            self.module.builder.get_object("exposeButton").set_sensitive(True)

            def abortTimer():
                self.exposureLabel.hide()
                self.exposureProgress.hide()
                return False
            glib.timeout_add(2000, abortTimer)

            if self.exposeTimer:
                glib.source_remove(self.exposeTimer)
                self.exposeTimer = 0
            
            if self.readoutTimer:
                glib.source_remove(self.readoutTimer)
                self.readoutTimer = 0
            
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


class CameraGUIModule(ChimeraGUIModule):

    module_controls = {"camera": "Camera",
                       "wheel": "FilterWheel"}

    def __init__ (self, manager):
        ChimeraGUIModule.__init__(self, manager)

        self.view = None
        self.controller = None

    def setupGUI (self, objects):

        camera = objects.get("camera", None)
        wheel  = objects.get("wheel", None)

        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(os.path.dirname(__file__), "camera.xml"))

        self.view = CameraView(self)
        self.controller = CameraController(self)
        self.imageViewer = ImageViewer(self)

        self.controller.setCamera(camera)
        self.controller.setFilterWheel(wheel)

        # some UI tweaks
        self.builder.get_object("durationSpin").set_value(1)
        self.builder.get_object("framesSpin").set_value(1)
        self.builder.get_object("shutterOpen").set_active(1)

        if wheel:
            # create filter box
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

        win = self.builder.get_object("window")
        gui = self.builder.get_object("gui")
        win.remove(gui)
        
        return [("Camera", gui, gdl.DOCK_LEFT)]
        
    def setupEvents (self):

        def camera_expose_action(action):
            self.builder.get_object("abortExposureButton").set_sensitive(True)
            self.builder.get_object("exposeButton").set_sensitive(False)
            threading.Thread(target=self.controller.expose).start()
    
        def camera_abort_action(action):
            threading.Thread(target=self.controller.abortExposure).start()
    
        self.builder.connect_signals({"camera_expose_action": camera_expose_action,
                                      "camera_abort_action" : camera_abort_action})

