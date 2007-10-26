import sys
import time

from chimera.core.lifecycle import BasicLifeCycle
from chimera.util.output import update_scroll_spinner

class MeadeTest (BasicLifeCycle):

    __options__ = {"device": "/dev/ttyS1"}

    def __init__ (self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init (self, config):

        self.config += config

        return True

    def main (self):

        m = self.manager.getDriver ('/Meade/lx16?device=%s' % self.config.device)

        def printInfo():
            print "align mode:", m.getAlignModes()[m.getAlignMode()]
            print "ra :", m.getRa()
            print "dec:", m.getDec()
            print "az :", m.getAz()
            print "alt:", m.getAlt()
       
            print "lat :", m.getLat()
            print "long:", m.getLong()
       
            print "date:" , m.getDate()
            print "time:" , m.getLocalTime()
            print "to utc:", m.getUTCOffset()
            print "lst:", m.getLocalSiderealTime()

            print "tracking rate:", m.getCurrentTrackingRate ()

        def setInfo ():

            if not m.setLat("-22 32 03"):
                print m.getError ()

            if not m.setLong("-45 34 57"):
                print m.getError ()
       
            if not m.setDate(time.time ()):
                print m.getError ()

            if not m.setLocalTime(time.time ()):
                print m.getError ()
            
            if not m.setUTCOffset(3):
                print m.getError ()

            #if not m.setCurrentTrackingRate(0):
            #    print m.getError ()
            
        def printCoord():
            print "%20s %20s %20s %20s %20s" % (m.getLocalSiderealTime(), m.getRa(), m.getDec(), m.getAz(), m.getAlt() )

        def sync ():
            print
            printCoord ()
            print "syncing..."
            if not m.sync ("10 00 00", "00 00 00"):
                print m.getError ()
            printCoord ()

        def slewRate ():
            print
            print "slews rate:", m.getSlewRates()
            print "current slew rate:", m.getSlewRate (), m.getSlewRates()[m.getSlewRate()]
            if not m.setSlewRate ( max(m.getSlewRates().keys()) ):
                print m.getError ()
            print "current slew rate:", m.getSlewRate (), m.getSlewRates()[m.getSlewRate()]

        def movement ():

            for rate in m.getSlewRates().keys():
                
                print "moving to East at %s rate:" % m.getSlewRates()[rate],
                sys.stdout.flush()
            
                t = time.time ()
                if not m.moveEast (3, rate):
                    print m.getError ()

                print time.time () - t
                sys.stdout.flush()
                
                print "moving to West at %s rate:" % m.getSlewRates()[rate],
                sys.stdout.flush()
            
                t = time.time ()
                if not m.moveWest (3, rate):
                    print m.getError ()

                print time.time () - t
                sys.stdout.flush()

                print "moving to North at %s rate:" % m.getSlewRates()[rate],
                sys.stdout.flush()
                        
                t = time.time ()
                if not m.moveNorth (3, rate):
                    print m.getError ()

                print time.time () - t
                sys.stdout.flush()

                print "moving to South at %s rate:" % m.getSlewRates()[rate],
                sys.stdout.flush()
            
                t = time.time ()
                if not m.moveSouth (3, rate):
                    print m.getError ()

                print time.time () - t
                sys.stdout.flush()

                print

        def alignMode ():

            #for i in range (10):
            #    print "current align mode:", m.getAlignModes()[m.getAlignMode()]

            for mode in m.getAlignModes().keys():
               print "current align mode:", m.getAlignModes()[m.getAlignMode()]
               print "switching to:", m.getAlignModes()[mode]

               if not m.setAlignMode (mode):
                   print m.getError ()

               print "current align mode:", m.getAlignModes()[m.getAlignMode()]
               print

        def tracking ():

            m.setAlignMode (m.getAlignModes().values().index("POLAR"))
            print "current align mode:", m.getAlignModes()[m.getAlignMode()]

            print "setting new date and time..."
            setInfo ()

            print
            for i in range(10):
                printCoord ()
                time.sleep (1)

            print "stopping tracking..."
            sys.stdout.flush()
            
            m.stopTracking()

            start = time.time ()
            finish = start + 30

            print "waiting",
            sys.stdout.flush ()

            while time.time() < finish:
                print ".",
                sys.stdout.flush ()
                time.sleep (1)
            print
                
            print "re-starting tracking..."
            sys.stdout.flush()

            m.startTracking()

            print "using old date and time..."
            print
            for i in range(10):
                printCoord ()
                time.sleep (1)

            print
            print "setting new date and time..."
            setInfo ()

            print
            for i in range(10):
                printCoord ()
                time.sleep (1)

        def park ():

            print "="*50
            print "Park and unpark test"
            print "="*50
            
            print "Initial conditions (post power-on):"
            printInfo()
            print

            print "Starting the scope..."
            setInfo()
            print

            print "Scope location, date, time updated, new conditions:"
            printInfo()
            print


            print "Pooling telescope position:"

            for i in range(10):
                printCoord ()
                time.sleep (1)

            print

            print "Slewing... to 15:00:00 -20:00:00"
            if not m.slewToRaDec ("15:00:00", "-20:00:00"):
                print m.getError ()

            print
            
            print "Parking the scope at %s (lst: %s)" % (time.strftime("%c"), m.getLocalSiderealTime())

            if not m.park ():
                print m.getError ()
            print

            print "Pooling telescope position:"

            for i in range(10):
                printCoord ()
                time.sleep (1)

            print

            start = time.time ()
            finish = start + (30*60) # wait 30 minutes

            print "Waiting              ",

            while time.time() < finish:
                update_scroll_spinner()
                time.sleep (0.2)
            print
                
            print

            print "Unparking the scope at %s (lst: %s)" % (time.strftime("%c"), m.getLocalSiderealTime())

            if not m.unpark ():
                print m.getError ()
            print

            print "Pooling telescope position:"

            for i in range(10):
                printCoord ()
                time.sleep (1)

            print "="*50

        def slewToAzAlt():

            printCoord ()

            if not m.slewToAzAlt ("180:00:00", "40:00:00"):
                print m.getError ()

            printCoord()

        def slewToRaDec():

            printCoord ()

            if not m.slewToRaDec ("20:00:00", "00:00:00"):
                print m.getError ()

            printCoord()
            
            
        printInfo ()
        setInfo ()
        print
        printInfo()
        #sync ()
        #print
        #printInfo ()        

        #slewRate ()
        #movement ()
        #alignMode()

        #tracking()

        #park ()

        #slewToAzAlt()
        #slewToRaDec()


        
