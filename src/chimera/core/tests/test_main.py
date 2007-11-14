
from chimera.core.manager        import Manager
from chimera.core.chimeraobject  import ChimeraObject
from chimera.core.proxy          import Proxy
from chimera.core.main           import chimera
from chimera.core.constants      import MANAGER_DEFAULT_PORT
import socket


class Simple (ChimeraObject):
    def __init__ (self):
        ChimeraObject.__init__(self)

    def answer (self):
        return 42

class TestMain (object):

    def test_main (self):

        # add simple
        manager = Manager(port = 9000)
        
        assert manager.addClass(Simple, "simple") != False

        s = chimera.Simple(port=9000)
        assert isinstance(s, Proxy)
        assert s.answer() == 42

        s = chimera.Simple("simple", port=9000)
        assert isinstance(s, Proxy)
        assert s.answer() == 42

        s = chimera.Simple("simple", host = socket.gethostname(), port = 9000)
        assert isinstance(s, Proxy)
        assert s.answer() == 42
        
