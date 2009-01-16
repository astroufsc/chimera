from chimera.core.proxy import Proxy
from chimera.core.util import getManagerURI
from chimera.core.exceptions import ChimeraException
from chimera.core.constants import (MANAGER_BEACON_PORT,
                                    MANAGER_BEACON_CHALLENGE,
                                    MANAGER_BEACON_ERROR)

import socket
import select

class ManagerNotFoundException(ChimeraException): pass

class ManagerLocator (object):

    @staticmethod
    def locate():
        """Use to locate running instance of Chimera.

        When started, Manager creates a UDP broadcast server. This
        method tries to locate the Manager using a broadcast message
        and waiting for an answer.
        """
        
        sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sk.setblocking(0)

        try:
            try:
                sk.sendto(MANAGER_BEACON_CHALLENGE, ("", MANAGER_BEACON_PORT))
            
                ins, outs, excs = select.select([sk], [], [sk], 1)
            
                if sk in ins:
                    data, _ = sk.recvfrom(1024)
                    if data.strip() != MANAGER_BEACON_ERROR:
                        host, port = data.split(":")
                        return Proxy(uri=getManagerURI(host, int(port)))

                raise ManagerNotFoundException("Couldn't locate any suitable Manager.")

            except socket.error, e:
                raise ManagerNotFoundException("Error trying to locate a suitable Manager.")

        finally:
            sk.close()

        
        
        
