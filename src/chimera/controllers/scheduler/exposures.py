
from chimera.controllers.scheduler.model import Exposure

import chimera.core.log
import logging

log = logging.getLogger(__name__)

from elixir.options import using_options

import time


__all__ = ['Science']


class Science (Exposure):

    using_options(tablename='exposure_science', inheritance='multi')

    def process (self):
        log.debug("processing exposure %d" % self.id)

        for n in range(1, self.frames+1):
            log.debug("[begin] frame %d/%d (%s)" % (n, self.frames, self.filter_))
            time.sleep(self.exptime)
            log.debug("[end] frame %d/%d (%s)" % (n, self.frames, self.filter_))
            self.framesDone += 1
        
