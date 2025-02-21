import signal
import time

from chimera.core.event import event
from chimera.core.manager import Manager
from chimera.core.chimeraobject import ChimeraObject


class Instrument(ChimeraObject):
    def do(self, n: int):
        time.sleep(n)
        self.completed(n)

    @event
    def completed(self, n: int): ...


if __name__ == "__main__":
    m = Manager(port=9999)

    m.addClass(Instrument, "unique")
    m.start("/Instrument/unique")
    m.wait()
