

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ObjectNotFoundException, ChimeraException

from chimera.controllers.scheduler.machine import Machine, State

import threading

__all__ = ['Scheduler']


class Scheduler (ChimeraObject):

    __config__ = {"telescope"   : "/Telescope/0?driver=/FakeTelescope/0",
                  "camera"      : "/Camera/0?driver=/FakeCamera/0",
                  "filterwheel" : "/FilterWheel/0?driver=/FakeFilterWheel/0",
                  "focuser"     : "/Focuser/0?driver=/FakeFocuser/0",
                  "dome"        : "/Dome/0?driver=/FakeDome/0"}

    def __init__ (self):
        ChimeraObject.__init__(self)
        
        self.machine = Machine()
        self.proxies = {}

    def __start__ (self):

        # try to get proxies
        try:
            self.proxies["telescope"]   = self.getManager().getProxy(self["telescope"])
            self.proxies["camera"]      = self.getManager().getProxy(self["camera"])
            self.proxies["filterwheel"] = self.getManager().getProxy(self["filterwheel"])
            self.proxies["focuser"]     = self.getManager().getProxy(self["focuser"])
            self.proxies["dome"]        = self.getManager().getProxy(self["dome"])

            self.machine.proxies = self.proxies
            
        except ObjectNotFoundException, e:
            raise ChimeraException("Cannot start scheduler. %s." % e)

    def control (self):
        self.machine.state(State.DIRTY)
        t = threading.Thread(target=self.machine.run)
        t.setDaemon(False)
        t.start()
        return False # that's al folks

    def __stop__ (self):
        self.machine.state(State.SHUTDOWN)
