import sys
import time

from chimera.core.lifecycle import BasicLifeCycle
from chimera.util.output import update_spinner

class MeadePEC (BasicLifeCycle):

    __options__ = {"axis": ["ra", "dec"]}

    def __init__ (self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init (self, config):

        self.config += config

        return True

    def main (self):

        m = self.manager.getDriver ('/Meade/lx16?device=/dev/ttyS1')

        protocol = {"ra": "VR",
                    "dec": "VD"}

        f = open("pec.%s" % self.config.axis, "w")

        # These comments are only for RA axis
        # Each pec phase represents an interval of time of the worm period.
        # Meade 16" have 360 teeths on the worm gear, so dividing it by the sidereal time (in seconds)
        # we have the worm period. Dividing this by the number of PEC corrections per turn, we have the
        # interval of phase (pec_dt)
        sidereal_time = (23*3600 + 56*60 + 4.1)
        pec_dt = (sidereal_time / 360) / 200

        # During each worm phase the mount will turn the OTA axis by an angle d_theta.
        # If we get the number of arcsec in a full circle divided by the sidereal time
        # we will have the number of arcseconds that the mount will move in one second (sidereal)
        # Multiplying this by pec_dt we got the number of arcseconds that the mount turn the OTA axis during
        # one phase of the worm period.
        full_circle = 360 * 3600
        d_theta = (full_circle / sidereal_time) * pec_dt

        # The raw PEC value represents an acceleration or deacelleration of the sidereal rate of the
        # mount, thus, correcting west/east movements. To convert the value to arcseconds, just consider the
        # raw value as a mutiple of the sidereal time on the above formula.

        print >> f, "# Meade PEC table for %s axis" % self.config.axis.upper()
        print >> f, "# %s" % time.strftime ("%X %x")

        if self.config.axis == "ra":
            print >> f, "# index\tworm phase (s)\traw value\toffset (arcsec)\taccumulated (arcsec)"
        else:
            print >> f, "# phase (index)\toffset"        

        # RA offset sum
        sum = 0.0

        for i in range (200):
            m._write (":%s%03d#" % (protocol[self.config.axis], i))
            print "\rGetting PEC for %s axis... (%03d)   " % (self.config.axis.upper(), i),
            update_spinner ()

            if self.config.axis == "ra":
                value = float(m._readline ()[:-1])

                pec_d_theta = (full_circle / (value * sidereal_time)) * pec_dt
                offset = d_theta - pec_d_theta
                sum += offset
                
                print >> f, "%03d\t%.6f\t%.6f\t%.6f\t%.6f" % (i, i*pec_dt, value, offset, sum)
            else:
                print >> f, "%03d\t%s" % (i, m._readline ()[:-1])                

        print

        self.manager.shutdown ()
        sys.exit (0)
    

