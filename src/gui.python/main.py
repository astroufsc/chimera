#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys
import time

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import gtk.glade
    import gobject
    import time
    import threading, thread
except:
    sys.exit(1)

gtk.gdk.threads_init()

from chimera.core.systemconfig import SystemConfig
from chimera.core.callback import callback
from chimera.core.manager import Manager
from chimera.core.managerlocator   import ManagerLocator, ManagerNotFoundException
from chimera.interfaces.filterwheel import InvalidFilterPositionException
from chimera.core.constants import SYSTEM_CONFIG_DEFAULT_FILENAME
from chimera.core.exceptions import InvalidLocationException, printException
from chimera.util.ds9 import DS9

import subprocess


def toggle_shutter_button(widget):

 if widget.get_label() == "open":
  widget.set_label("closed")
 else:
  widget.set_label("open")

class ChimeraGUI:

    def __init__(self):
        
        self.ds9 = None;
        
        self.builder = gtk.Builder()
        self.builder.add_from_file("chimera.xml")
        
        dic = {"on_button_clicked" : self.on_button_clicked,
               "onStopExposeClicked": self.onStopExposeClicked,
               "on_window_destroy" : gtk.main_quit,
               "on_shutter_toggle": toggle_shutter_button
              }
        
        self.builder.connect_signals(dic)
        self.imageWdg = self.builder.get_object("image1")
        self.mainWindow = self.builder.get_object("mainWindow")
        self.mainWindow.maximize()
        self.mainWindow.show()

        # system config
        self.localManager = Manager(host="localhost", port=9000)

        try:
            self.sysconfig = SystemConfig.fromFile(SYSTEM_CONFIG_DEFAULT_FILENAME)
        except (InvalidLocationException, IOError), e:
            log.exception(e)
            log.error("There was a problem reading your configuration file. (%s)" % e)
            sys.exit(1)
        
        self.manager = ManagerLocator.locate(self.sysconfig.chimera["host"], self.sysconfig.chimera["port"])
        
        @callback(self.localManager)
        def exposeBegin(request):
            self.currentFrameExposeStart = time.time()
            self.currentFrame += 1
            #print(40*"=")
            #print("exposeBegin [%03d] [%s]" % (self.currentFrame, time.strftime("%c")))
            #self.out("exposing (%.3fs) ..." % request["exptime"], end="")
            
        @callback(self.localManager)
        def exposeComplete(request):
            #print("expose OK (took %.3f s)" % (time.time()-self.currentFrameExposeStart))
            pass
        @callback(self.localManager)
        def readoutBegin(request):
            self.currentFrameReadoutStart = time.time()
            #print("readoutBegin")
                
        @callback(self.localManager)
        def readoutComplete(image):
            print(" (%s) " % image.compressedFilename())
            print(" readoutComplete OK (took %.3f s)"  % (time.time()-self.currentFrameReadoutStart))
            print("[%03d] took %.3fs" % (self.currentFrame, time.time()-self.currentFrameExposeStart))
            print(40*"=")
            if (self.totalFrames > 0):
                fraction = self.currentFrame/self.totalFrames
                gobject.idle_add(self.setProgressBar, fraction,  "wait...") 
        
        @callback(self.localManager)
        def abortComplete():
            print(40*"@")
            print("abortComplete OK (took %.3f s)"  % (time.time()-self.currentFrameExposeStart))
            print(40*"@")
            self.currentFrame = 0
            self.currentFrameExposeStart = 0
            self.currentFrameReadoutStart = 0

        def getFirst(type):
            objs = self.manager.getResourcesByClass(type)
            if objs:
                return self.manager.getProxy(objs[0])
            else:
                raise Exception("ERRO")

        self.camera = getFirst("Camera")
        self.camera.exposeBegin     += exposeBegin
        self.camera.exposeComplete  += exposeComplete
        self.camera.abortComplete   += abortComplete
        self.camera.readoutBegin    += readoutBegin
        self.camera.readoutComplete += readoutComplete

        #wheelName = "150.162.110.2:7666/%s/%s" % (self.sysconfig.filterwheels[0].cls, self.sysconfig.filterwheels[0].name)
        #wheelName = "150.162.110.2:7666/IFilterWheel/0"
        self.wheel = getFirst("FilterWheel")

    def on_button_clicked(self, button):
        threading.Thread(target=self.doExpose).start()

    def onStopExposeClicked(self, button):
        threading.Thread(target=self.doStopExpose).start()
    
    def doExpose(self):
        gobject.idle_add(self.setProgressBar, 0.0,  "wait...")
        
        durationSpin = self.builder.get_object("durationSpin")
        duration = durationSpin.get_value()
        
        framesSpin = self.builder.get_object("framesSpin")
        self.totalFrames = framesSpin.get_value()
        
        shutterButton = self.builder.get_object("shutterButton")
        if(shutterButton.get_active()):
          shutterState = "CLOSE"
        else: 
          shutterState = "OPEN"
        
        self.currentFrame = 0
        self.currentFrameExposeStart = 0
        self.currentFrameReadoutStart = 0
        
#         if(self.wheel):
#             filterMap = {"radioFilterU": "U", "radioFilterB": "B", "radioFilterV": "V", "radioFilterR": "R", "radioFilterI": "I"}
#             filterU = self.builder.get_object("radioFilterU")
#             filterButtons = filterU.get_group()
#             for f in filterButtons:
#                 if(f.get_active()):
#                     try:
#                         self.wheel.setFilter(filterMap[f.get_name()])
#                     except InvalidFilterPositionException, e:
#                         gobject.idle_add(self.setProgressBar, 1, "Finished", False)
#                         gobject.idle_add(self.showDialog,gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, "Couldn't move filter wheel to %s. (%s)" % (f.get_name(), e))
#                         return
#                     break
       
        imgs = None
        try: 
            imgs = self.camera.expose({"exptime": duration, "frames": self.totalFrames, "shutter": shutterState})
        except Exception, e:
            printException(e)

        if(imgs):
            frames = 1
            for img in imgs:
                imgUrl = img.http()
                if not self.ds9:
                    self.ds9 = DS9(open=True)
                try:
                 self.ds9.set("file url %s " % imgUrl)
                except Exception: pass
                # = subprocess.Popen("ds9 -url %s" % imgUrl, shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        
        gobject.idle_add(self.setProgressBar, 1, "Downloading images. Please wait...")
        self.currentFrame = 0
        self.currentFrameExposeStart = 0
        self.currentFrameReadoutStart = 0
        self.totalFrames = 0
        gobject.idle_add(self.setProgressBar, 1, "Finished", False)
    
    def doStopExpose(self):
        print("doStopExpose")
        cameraName = "%s:%d/%s/%s" % (self.sysconfig.chimera["host"], self.sysconfig.chimera["port"], self.sysconfig.cameras[0].cls, self.sysconfig.cameras[0].name)
        camera = self.manager.getProxy(cameraName)
        if(camera):
            fraction = 0.0
            if (self.totalFrames > 0):
                fraction = self.currentFrame/self.totalFrames
            gobject.idle_add(self.setProgressBar, 1, "aborting...")
            camera.abortExposure()
            gobject.idle_add(self.setProgressBar, 0, "Finished")
            time.sleep(1)
            gobject.idle_add(self.setProgressBar, 0, "Finished", False)
            print("aborted")
            print(40*"=")
    
    def setProgressBar(self, fraction, text, show=True):
        progressBar = self.builder.get_object("footerProgressBar")
        if(show):
            progressBar.show()
            progressBar.set_fraction(fraction)
            progressBar.set_text(text);
        else:
            progressBar.hide()
    def showDialog(self, gtkMessageType, gtkButtons, message):
        dialog = gtk.MessageDialog(self.mainWindow, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtkMessageType, gtkButtons, message)
        #dialog.show_all()
        dialog.connect('response', lambda w,d: dialog.destroy())
        dialog.show()
    
    def on_window_destroy(self, widget):
        gtk.main_quit()

if __name__ == "__main__":
    win = ChimeraGUI()
    gtk.main()

