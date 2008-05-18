
from chimera.controllers.scheduler.model import Exposure

from chimera.instruments.telescope   import Telescope
from chimera.instruments.camera      import Camera
from chimera.instruments.filterwheel import FilterWheel

import chimera.core.log
import logging

log = logging.getLogger(__name__)

from elixir.options import using_options

import time


__all__ = ['Science']


class Science (Exposure):

    using_options(tablename='exposure_science', inheritance='multi')

    def process (self, instruments):

        self.instruments = instruments
        
        log.debug("processing exposure %d" % self.id)

        # [pre] slew
        self.preSlew()

        # slew
        self.slew()

        # [post] slew
        self.postSlew()

        # [pre] filter
        self.preFilter()

        # filter
        self.changeFilter()

        # [post] filter
        self.postFilter()

        # [pre] frameset
        self.preFrameset()

        for n in range(1, self.frames+1):
            # [pre] frame
            self.preFrame(n)

            # frame
            self.frame(n)
           
            # [post] frame
            self.postFrame(n)

        # [post] frameset
        self.postFrameset()
        

    def preSlew (self):
        pass

    def slew (self):
        log.debug("[slew] slewing to %s" % self.observation.target.position)

        self.instruments["telescope"].slewToRaDec(self.observation.target.position)

    def postSlew (self):
        pass

    def preFilter (self):
        pass

    def changeFilter (self):
        log.debug("[filter] changing to filter %s" % self.filter_)

        wheel = self.instruments["filterwheel"]

        if wheel.getFilter() != self.filter_:
            wheel.setFilter(self.filter_)
        
    def postFilter (self):
        pass

    def preFrameset (self):
        pass

    def preFrame (self, n):
        pass
    
    def frame (self, n):
        cam = self.instruments["camera"]
        log.debug("[begin] frame %d/%d (%s)" % (n, self.frames, self.filter_))
        time.sleep(self.exptime)
        log.debug("[end] frame %d/%d (%s)" % (n, self.frames, self.filter_))
        self.framesDone += 1

    def postFrame (self, n):
        pass

    def postFrameset (self):
        pass

    
 
