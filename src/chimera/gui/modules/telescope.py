
from chimera.util.coord import Coord
from chimera.core.callback import callback
from chimera.core.exceptions import ObjectNotFoundException, printException

from chimera.util.position import Position, Epoch

from chimera.gui.module import ChimeraGUIModule
from chimera.gui.modules.lcd import LCDWidget

import gtk
import glib
import gdl

import threading
import os


class TelescopeController:
    def __init__ (self, main):
        self.telescope = None
        self.main = main
    
    def setTelescope(self, telescope):
        self.telescope = telescope
        self.main.view.startStatusUpdate()
        
    def getTelescope(self):
        # transfer to current thread and return (a hacky way to reuse Proxies)
        self.telescope._transferThread()
        return self.telescope
    
    def slew(self):

        slewFunction = None
        target = None
        
        currentPage = self.main.view.slewOptions.get_current_page()

        if currentPage == 0:
            raHour = self.main.view.raHourSpin.get_value()
            raMinute = self.main.view.raMinuteSpin.get_value()
            raSec = self.main.view.raSecSpin.get_value()
        
            decDegree = self.main.view.decDegreeSpin.get_value()
            decMinute = self.main.view.decMinuteSpin.get_value()
            decSec = self.main.view.decSecSpin.get_value()
        
            ra = "%2d:%2d:%2d" %(raHour, raMinute, raSec)
            dec = "%2d:%2d:%2d" %(decDegree, decMinute, decSec)

            epochStr = str(self.main.view.epochCombo.get_active()).lower()

            if epochStr == "j2000":
                epoch = Epoch.J2000
            elif epochStr == "b1950":
                epoch = Epoch.B1950
            elif epochStr == "now":
                epoch = Epoch.Now
            else:
                # FIXME
                epoch = epochStr
        
            target = Position.fromRaDec(ra, dec, equinox=epoch)
            slewFunction = self.telescope.slewToRaDec

        elif currentPage == 1:

            altDegree = self.main.view.altDegreeSpin.get_value()
            altMinute = self.main.view.altMinuteSpin.get_value()
            altSec = self.main.view.altSecSpin.get_value()
        
            azDegree = self.main.view.azDegreeSpin.get_value()
            azMinute = self.main.view.azMinuteSpin.get_value()
            azSec = self.main.view.azSecSpin.get_value()
            
            alt = "%2d:%2d:%2d" %(altDegree, altMinute, altSec)
            az = "%2d:%2d:%2d" %(azDegree, azMinute, azSec)
        
            target = Position.fromAltAz(alt, az)
            slewFunction = self.telescope.slewToAltAz

        elif currentPage == 2:
            target =  str(self.main.view.objectNameCombo.child.get_text())
            slewFunction = self.telescope.slewToObject
        
        self.main.view.slewBeginUi()
        
        @callback(self.main.manager)
        def slewBegin(target):
            self.main.view.slewBegin(target)
        
        @callback(self.main.manager)
        def slewComplete(target):
            self.main.view.slewComplete(target)
        
        @callback(self.main.manager)
        def abortComplete(target):
            self.main.view.abortComplete(target)
        
        self.telescope.slewComplete += slewBegin
        self.telescope.slewComplete += slewComplete
        self.telescope.abortComplete += abortComplete

        try:
            slewFunction(target)
        except ObjectNotFoundException, e:
            self.main.view.showError("Object %s was not found on our catalogs." % target)
        except Exception, e:
            printException(e)
            
        finally:
            self.telescope.slewComplete -= slewBegin
            self.telescope.slewComplete -= slewComplete
            self.telescope.abortComplete -= abortComplete

            self.main.view.slewComplete(target)

    def isSlewing(self):
        return self.telescope.isSlewing()
        
    def moveEast(self):
        offset = self.main.view.offsetCombo.child.get_text()
        self._move(self.telescope.moveEast, offset)
        
    def moveWest(self):
        offset = self.main.view.offsetCombo.child.get_text()
        self._move(self.telescope.moveWest, offset)
    
    def moveNorth(self):
        offset = self.main.view.offsetCombo.child.get_text()
        self._move(self.telescope.moveNorth, offset)
    
    def moveSouth(self):
        offset = self.main.view.offsetCombo.child.get_text()
        self._move(self.telescope.moveSouth, offset)

    def _move(self, method, offset):
        try:
            offset = float(offset)
            method(offset)
        except Exception, e:
            printException(e)
    
    def toggleTracking(self):
        if(self.isTracking()):
            self.getTelescope().stopTracking()
            self.main.view.updateTrackingStatus()
        else:
            self.getTelescope().startTracking()
            self.main.view.updateTrackingStatus()
            
    def getCurrentRaDec(self):
        telescope = self.getTelescope()
        return telescope.getPositionRaDec()
    
    def getCurrentAltAz(self):
        telescope = self.getTelescope()
        return telescope.getPositionAltAz()
    
    def isTracking(self):
        telescope = self.getTelescope()
        return telescope.isTracking()
    
class TelescopeView:
    def __init__ (self, main):
        self.main = main

        self.raHourSpin = self.main.builder.get_object("raHourSpin")
        self.raMinuteSpin = self.main.builder.get_object("raMinuteSpin")
        self.raSecSpin = self.main.builder.get_object("raSecSpin")
        
        self.decDegreeSpin = self.main.builder.get_object("decDegreeSpin")
        self.decMinuteSpin = self.main.builder.get_object("decMinuteSpin")
        self.decSecSpin = self.main.builder.get_object("decSecSpin")       
        
        self.azDegreeSpin = self.main.builder.get_object("azDegreeSpin")
        self.azMinuteSpin = self.main.builder.get_object("azMinuteSpin")
        self.azSecSpin = self.main.builder.get_object("azSecSpin")
        
        self.altDegreeSpin = self.main.builder.get_object("altDegreeSpin")
        self.altMinuteSpin = self.main.builder.get_object("altMinuteSpin")
        self.altSecSpin = self.main.builder.get_object("altSecSpin")

        self.objectNameCombo = self.main.builder.get_object("objectNameCombo")
        self.slewOptions = self.main.builder.get_object("slewOptions")

        self.epochCombo = self.main.builder.get_object("epochCombo")
        listStore = gtk.ListStore(str)
        listStore.insert(0,["J2000"])
        listStore.insert(1,["B1950"])
        listStore.insert(2, ["Now"])
        self.epochCombo.set_model(listStore)
        self.epochCombo.set_text_column(0)
        self.epochCombo.set_active(0)
        
        self.offsetCombo = self.main.builder.get_object("offsetCombo")
        listStore = gtk.ListStore(str)
        listStore.insert(0,["10 arcsec"])
        listStore.insert(1,["20 arcsec"])
        listStore.insert(2, ["30 arcsec"])
        self.offsetCombo.set_model(listStore)
        self.offsetCombo.set_text_column(0)
        self.offsetCombo.set_active(0)

        self.raLCDWidget = gtk.DrawingArea()
        self.raLCD = LCDWidget(self.raLCDWidget, 1, 14)
        self.raLCD.set_zoom_factor(1)
        self.main.builder.get_object("raBox").pack_end(self.raLCDWidget)

        self.decLCDWidget = gtk.DrawingArea()
        self.decLCD = LCDWidget(self.decLCDWidget, 1, 14)
        self.decLCD.set_zoom_factor(1)
        self.main.builder.get_object("decBox").pack_end(self.decLCDWidget)

        self.altLCDWidget = gtk.DrawingArea()
        self.altLCD = LCDWidget(self.altLCDWidget, 1, 14)
        self.altLCD.set_zoom_factor(1)
        self.main.builder.get_object("altBox").pack_end(self.altLCDWidget)

        self.azLCDWidget = gtk.DrawingArea()
        self.azLCD = LCDWidget(self.azLCDWidget, 1, 14)
        self.azLCD.set_zoom_factor(1)
        self.main.builder.get_object("azBox").pack_end(self.azLCDWidget)

    def showError(self, message):
        #md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,
        #                       gtk.BUTTONS_CLOSE, message)
        #md.run()
        #md.destroy()
        pass

    def updateStatusView(self):

        if not self.main.controller.isSlewing():
            raDec = self.main.controller.getCurrentRaDec()
            altAz = self.main.controller.getCurrentAltAz()

            self.raLCD.print_line("%14s" % str(raDec.ra))
            self.decLCD.print_line("%14s" % str(raDec.dec))
            self.altLCD.print_line("%14s" % str(altAz.alt))
            self.azLCD.print_line("%14s" % str(altAz.az))

            self.updateTrackingStatus()
            
        return True
      
    def pauseStatusUpdate(self):
        if self.status_timeout:
            glib.source_remove(self.status_timeout)

    def startStatusUpdate(self):
        self.status_timeout = glib.timeout_add(1500, self.updateStatusView, priority=glib.PRIORITY_LOW)
        
    def updateTrackingStatus(self):

        if(self.main.controller.isTracking()):
            self.main.builder.get_object("trackingCheckbox").set_active(True)
        else:
            self.main.builder.get_object("trackingCheckbox").set_active(False)
        
    def slewBeginUi(self):
        def ui():
            self.main.builder.get_object("slewButton").set_sensitive(False)
            telescopeProgress = self.main.builder.get_object("telescopeProgress")
            telescopeProgress.set_text("Slewing ...")
            telescopeProgress.show()
            
            def telescopeTimer():
                self.main.builder.get_object("telescopeProgress").pulse()
                return True
            
            self.telescopeTimer = glib.timeout_add(75, telescopeTimer)

        self.pauseStatusUpdate()
            
        glib.idle_add(ui)
    
    def slewBegin(self, target = None):
        pass
    
    def slewComplete(self, target = None):
        def ui():
            telescopeProgress = self.main.builder.get_object("telescopeProgress")
            telescopeProgress.hide()
            
            if self.telescopeTimer:
                glib.source_remove(self.telescopeTimer)
                self.telescopeTimer = 0
            
            self.main.builder.get_object("slewButton").set_sensitive(True)
            
        glib.idle_add(ui)
        
        self.startStatusUpdate()
    
    def abortComplete(self, target = None):
        def ui():
            pass
        glib.idle_add(ui)


class TelescopeGUIModule(ChimeraGUIModule):

    module_controls = {"telescope": "Telescope"}

    def __init__ (self,  manager):
        ChimeraGUIModule.__init__(self, manager)

        self.view = None
        self.controller = None
        
    def setupGUI (self, objects):

        telescope = objects.get("telescope", None)

        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(os.path.dirname(__file__), "telescope.xml"))

        self.view = TelescopeView(self)
        self.controller = TelescopeController(self)
        self.telescopeInit = False
        
        self.controller.setTelescope(telescope)

        # Query telescope tracking status and adjust UI accordingly
        self.view.updateTrackingStatus()
        self.telescopeInit = True

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

        win = self.builder.get_object("window")
        gui = self.builder.get_object("gui")
        win.remove(gui)
        
        return [("Telescope", gui, gdl.DOCK_TOP)]
        
    def setupEvents (self):

        def telescope_slew_action(action):
            threading.Thread(target=self.controller.slew).start()
        
        def telescope_move_east_action(action):
            threading.Thread(target=self.controller.moveEast).start()
                
        def telescope_move_west_action(action):
            threading.Thread(target=self.controller.moveWest).start()
        
        def telescope_move_north_action(action):
            threading.Thread(target=self.controller.moveNorth).start()
        
        def telescope_move_south_action(action):
            threading.Thread(target=self.controller.moveSouth).start()
        
        def telescope_tracking_action(action):
            if(self.telescopeInit):
                threading.Thread(target=self.controller.toggleTracking).start()

        self.builder.connect_signals({"telescope_slew_action"      : telescope_slew_action,
                                      "telescope_move_east_action" : telescope_move_east_action,
                                      "telescope_move_west_action" : telescope_move_west_action,
                                      "telescope_move_north_action": telescope_move_north_action,
                                      "telescope_move_south_action": telescope_move_south_action,
                                      "telescope_tracking_action"  : telescope_tracking_action})
        
