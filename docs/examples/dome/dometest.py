from chimera.core.lifecycle import BasicLifeCycle

import time
import sys
import random


class DomeTest (BasicLifeCycle):

    def __init__ (self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init (self, config):

        self.config += config
        return True

    def main (self):

        dome = self.manager.getDriver ('/DomeLNA40cm/domedriver')

        print "="*50
        print "Dome test"
        print "="*50        

        def test (name, azs):

            print "Moving dome to azimuth 0 (north):"
            sys.stdout.flush()
            dome.slewToAz (0)
            print "done"

            start_time = time.time()
            print "="*50
            print "Starting %s test at (%s)" % (name, time.strftime ("%c", time.localtime(start_time)))
            print "="*50

        
            for az in azs:
                print "Moving to %s:" % az
                sys.stdout.flush()

                t0 = time.time()

                if not dome.slewToAz(az):
                    print dome.getError ()

                dt = time.time () - t0
                dt -= 0.1 # to correct sleep time in slew

                assert dome.getAz() in (az-1, az, az+1)

                print " slew time: %.3f" % dt

                print "done\n"
                sys.stdout.flush()

            finish = time.time()
            
            print "="*50
            print "Finishing %s test at '%s'. Test took %.2f seconds." % (name, time.strftime("%c", time.localtime(finish)), finish - start_time)
            print "="*50
            print


        azs = range (0, 360)
        test ("sequential", azs)

        #random.shuffle (azs)
        #test ("random", azs)

        def slitTest ():

            def close():

                print "closing the slit:"
                sys.stdout.flush()

                t0 = time.time ()
                if not dome.slitClose ():
                    print dome.getError ()
                dt = time.time () - t0

                print " dt: %.3f" % dt           
                print "done"
                sys.stdout.flush()

            def open ():
                print "opening the slit:"
                sys.stdout.flush()
            
                t0 = time.time ()
                if not dome.slitOpen ():
                    print dome.getError ()
                dt = time.time () - t0

                print " dt: %.3f" % dt
                print "done"
                sys.stdout.flush()

            open ()
            close()
            close()
            open ()
            open()
            close()


