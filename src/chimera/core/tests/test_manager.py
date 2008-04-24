
from chimera.core.manager        import Manager
from chimera.core.chimeraobject  import ChimeraObject
from chimera.core.proxy          import Proxy

from nose.tools import assert_raises

from chimera.core.exceptions   import InvalidLocationException, \
                                      ObjectNotFoundException,  \
                                      NotValidChimeraObjectException, \
                                      ChimeraObjectException, \
                                      ClassLoaderException


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
        assert self.manager.addClass(Simple, "simple", start=True)

        # already started
        assert_raises(InvalidLocationException, self.manager.addClass, Simple, "simple")
       
        assert_raises(NotValidChimeraObjectException, self.manager.addClass, NotValid, "nonono")
        assert_raises(InvalidLocationException, self.manager.addClass, Simple, "")

        # by location
        assert self.manager.addLocation('/ManagerHelper/h')
        assert_raises(ClassLoaderException, self.manager.addLocation, '/What/h')
        assert_raises(InvalidLocationException, self.manager.addLocation, 'foo')

        # start with error
        #assert self.manager.addLocation('/ManagerHelperWithError/h', start=False)
        #assert_raises(ChimeraObjectException, self.manager.start, '/ManagerHelperWithError/h')

        # start who?
        assert_raises(InvalidLocationException, self.manager.start, "/Who/am/I")

        # exceptional cases
        # __init__
        assert_raises(ChimeraObjectException, self.manager.addLocation, "/ManagerHelperWithInitException/h")

        # __start__
        assert_raises(ChimeraObjectException, self.manager.addLocation, "/ManagerHelperWithStartException/h")

        # __main__
        #assert_raises(ChimeraObjectException, self.manager.addLocation, "/ManagerHelperWithMainException/h")
        

    def test_remove_stop (self):

        assert self.manager.addClass(Simple, "simple")

        # who?
        assert_raises(InvalidLocationException, self.manager.remove, 'Simple/what')
        assert_raises(InvalidLocationException, self.manager.remove, 'foo')

        # stop who?
        assert_raises(InvalidLocationException, self.manager.stop, 'foo')

        # ok
        assert self.manager.remove('/Simple/simple') == True

        # __stop__ error
        assert self.manager.addLocation("/ManagerHelperWithStopException/h")
        assert_raises(ChimeraObjectException, self.manager.stop, '/ManagerHelperWithStopException/h')

        # another path to stop
        assert_raises(ChimeraObjectException, self.manager.remove, '/ManagerHelperWithStopException/h')

        # by index
        assert self.manager.addClass(Simple, "simple")
        assert self.manager.remove('/Simple/0') == True

    def test_proxy (self):

        assert self.manager.addClass(Simple, "simple")

        # who?
        assert_raises(InvalidLocationException, self.manager.getProxy, 'wrong')
        assert_raises(InvalidLocationException, self.manager.getProxy, 'Simple/simple')

        # ok
        assert self.manager.getProxy ('/Simple/simple')
        assert self.manager.getProxy ('/Simple/0')

        # calling
        p = self.manager.getProxy ('/Simple/0')
        assert isinstance(p, Proxy)

        assert p.answer() == 42

        # oops
        assert_raises (AttributeError, p.wrong)

    def test_manager (self):

        assert self.manager.addClass(Simple, "simple")
        
        p = self.manager.getProxy(Simple)
        assert p

        m = p.getManager()
        assert m.GUID() == self.manager.GUID()
