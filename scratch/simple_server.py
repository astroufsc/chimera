import signal
import time

from chimera.core.event import event
from chimera.core.manager import Manager
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.proxy import Proxy


class Instrument(ChimeraObject):
    def do(self, n: int):
        time.sleep(n)
        self.completed(n)

    @event
    def completed(self, n: int): ...


if __name__ == "__main__":
    m = Manager(port=9999)

    def signal_handler(sig, frame):
        m.shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    m.addClass(Instrument, "unique")
    m.start("/Instrument/unique")
    m.wait()
