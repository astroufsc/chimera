

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ObjectNotFoundException, ChimeraException

from chimera.controllers.scheduler.machine import Machine, State

import threading

__all__ = ['Scheduler']


class Scheduler (ChimeraObject):

    __config__ = {"telescope"   : "/Telescope/tel?driver=/FakeTelescope/fake",
                  "camera"      : "/Camera/cam?driver=/FakeCamera/fake",
                  "filterwheel" : "/FilterWheel/wheel?driver=/FakeFilterWheel/fake",
                  "focuser"     : "/Focuser/focus?driver=/FakeFocuser/fake",
                  "dome"        : "/Dome/dome?driver=/FakeDome/fake"}

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
