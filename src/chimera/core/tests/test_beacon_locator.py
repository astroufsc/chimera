
from chimera.core.manager import Manager
from chimera.core.managerlocator import ManagerLocator, ManagerNotFoundException

from socket import gethostbyname

from nose.tools import assert_raises

class TestBeaconLocator (object):

    def test_locate(self):
        
        manager = Manager(host='localhost', port=9999)

        proxy = ManagerLocator.locate()
        assert proxy.ping() == True

        assert proxy.URI.address == gethostbyname("localhost")
        assert proxy.URI.port    == 9999

        manager.shutdown()

        # where are you
        assert_raises(ManagerNotFoundException, ManagerLocator.locate)
