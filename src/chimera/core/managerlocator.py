from chimera.core.location import Location
from chimera.core.proxy import Proxy
from chimera.core.util import getManagerURI
from chimera.core.constants import MANAGER_DEFAULT_PORT
from chimera.core.exceptions import ChimeraException


class ManagerNotFoundException(ChimeraException):
    pass


class ManagerLocator (object):

    @staticmethod
    def locate(host, port=6379):
        """Simple class to easily contact a Manager
        """
        p = Proxy(Location(getManagerURI(host, port or MANAGER_DEFAULT_PORT)))
        if not p.ping():
            raise ManagerNotFoundException(
                "Couldn't find manager running on %s:%d" % (host, port))
        return p
