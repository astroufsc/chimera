
from chimera.core.lifecycle import BasicLifeCycle

from chimera.core.chimera import Chimera

from chimera.controllers.blocks import *
from chimera.util.observation import Observation

import sys
import threading

class ChimeraCam (BasicLifeCycle):

    __options__ = dict(driver="/SBIG/0",
                       nexp=1,
                       texp=1.0,
                       interval=0.0,
                       filename="image",
                       dirname="",
                       shutter="open",
                       display=True,
                       verbose=False)
    
    def __init__ (self, manager):
        BasicLifeCycle.__init__ (self, manager)

        # condition variable to handle ctrl+c
        self.exit = threading.Event()

        # our camera
        self.cam = None

        # log stuff
        self.log = logging.getLogger ("chimera-cam")
        self.log.propagate = 0
        logging.getLogger('').setLevel(logging.INFO)        

        console = logging.StreamHandler()
        console.setFormatter (logging.Formatter ('%(message)s', '%m-%d %H:%M'))
        console.setLevel(logging.INFO)
        
        self.log.addHandler(console)
        
    def init (self, config):
        self.config += config
        return True

    def shutdown (self):

        if not self.cam:
            return True

        if self.cam.isExposing():
            # to expose block returns
            self.exit.set ()
        
            # to kill current exposure
            abort_exposure (self.cam)
            
            self.log.warning (red("Aborting..."))

        return True

    def main (self):

        prepare_directory (self.config.dirname)

        self.cam = self.manager.getInstrument("/Camera/cam?driver=%s" % self.config.driver)

        if not self.cam:
            print "Couldn't conect to the selected camera driver %s." % self.config.driver
            Chimera().shutdown()

        target = Observation()
        target.nexp = self.config.nexp
        target.exptime = self.config.texp

        # ok, here we go!
        expose (self.cam,
                target,
                {"dirname" : self.config.dirname,
                 "filename": self.config.filename,
                 "interval": self.config.interval,
                 "shutter" : self.config.shutter,
                 "display" : True,
                 "display_min_time": 5},
                self.log,
                self.exit)

        Chimera().shutdown()
