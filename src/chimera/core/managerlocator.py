from chimera.core.proxy import Proxy
from chimera.core.util import getManagerURI
from chimera.core.constants import MANAGER_DEFAULT_PORT
from chimera.core.exceptions import ChimeraException

class ManagerNotFoundException(ChimeraException): pass

class ManagerLocator (object):

    @staticmethod
    def locate(host, port=None):
        """Simple class to easily contact an Manager
        """
        p = Proxy(uri=getManagerURI(host, port or MANAGER_DEFAULT_PORT))
        if not p.ping():
            raise ManagerNotFoundException("Couldn't find manager running on %s:%d" % (host, port))
        return p
    
