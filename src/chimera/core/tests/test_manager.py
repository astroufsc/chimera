
from chimera.core.manager        import Manager
from chimera.core.chimeraobject  import ChimeraObject
from chimera.core.proxy          import Proxy

from nose.tools import assert_raises


class Simple (ChimeraObject):

    def __init__ (self):
        ChimeraObject.__init__(self)

    def answer (self):
        return 42


class NotValid (object): pass
             
class TestManager (object):

    def setup (self):
        self.manager = Manager()

    def teardown (self):
        self.manager.shutdown()
        del self.manager

    def test_add_start (self):

        # add by class
        assert self.manager.addClass(Simple, "simple") != False
        assert self.manager.addClass(Simple, "simple") == False, "location already added."
       
        assert self.manager.addClass(NotValid, "nonono") == False
        assert self.manager.addClass(Simple, "") == False

        # by location
        assert self.manager.addLocation('/ManagerHelper/h') != False
        assert self.manager.addLocation('/What/h') == False
        assert self.manager.addLocation('foo') == False

        # start with error
        assert self.manager.addLocation('/ManagerHelperWithError/h', start=False) != False
        assert self.manager.start('/ManagerHelperWithError/h') == False, "start must return a true value to proceed."

        # start who?
        assert self.manager.start("/Who/am/I") == False

        # already started
        assert self.manager.start ("/Simple/simple") == True, "Already started should just ignore"       

        # exceptional cases
        # __init__
        assert self.manager.addLocation("/ManagerHelperWithInitException/h") == False

        # __start__
        assert self.manager.addLocation("/ManagerHelperWithStartException/h") == False

        # __main__
        assert self.manager.addLocation("/ManagerHelperWithMainException/h") == False
        

    def test_remove_stop (self):

        assert self.manager.addClass(Simple, "simple") != False

        # who?
        assert self.manager.remove('Simple/what') == False, "Invalid location"
        assert self.manager.remove('foo') == False, "Invalid location"

        # stop who?
        assert self.manager.stop('foo') == False

        # ok
        assert self.manager.remove('/Simple/simple') == True

        # __stop__ error
        assert self.manager.addLocation("/ManagerHelperWithStopException/h") != False
        assert self.manager.stop('/ManagerHelperWithStopException/h') == False

        # another path to stop
        assert self.manager.remove('/ManagerHelperWithStopException/h') == False

        # by index
        assert self.manager.addClass(Simple, "simple") != False
        assert self.manager.remove('/Simple/0') == True


    def test_proxy (self):

        assert self.manager.addClass(Simple, "simple") != False

        # who?
        assert self.manager.getProxy ('wrong') == False
        assert self.manager.getProxy ('Simple/simple') == False

        # ok
        assert self.manager.getProxy ('/Simple/simple') != False
        assert self.manager.getProxy ('/Simple/0') != False        

        # calling
        p = self.manager.getProxy ('/Simple/0')
        assert isinstance(p, Proxy)

        assert p.answer() == 42

        # oops
        assert_raises (AttributeError, p.wrong)

