import threading
import SocketServer

from chimera.core.exceptions import ChimeraException
from chimera.core.constants import MANAGER_BEACON_PORT, MANAGER_BEACON_CHALLENGE, MANAGER_BEACON_ERROR

class _ManagerBeaconHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request[0]
        client = self.request[1]

        try:
            if data == MANAGER_BEACON_CHALLENGE:
                client.sendto("%s:%s" % (self.server.manager.getHostname(), self.server.manager.getPort()), self.client_address)
            else:
                client.sendto(MANAGER_BEACON_ERROR, self.client_address)
        finally:
            client.close()
        
class ManagerBeacon(SocketServer.ThreadingUDPServer):

    def __init__ (self, manager):
        try:
            SocketServer.ThreadingUDPServer.__init__(self, ("<broadcast>", MANAGER_BEACON_PORT), _ManagerBeaconHandler)
        except Exception:
            raise ChimeraException("Failed to start Manager Beacon.")

        self.manager = manager
        self.shouldDie = threading.Event()

    def shutdown(self):
        self.shouldDie.set()

    def run(self):
        while not self.shouldDie.isSet():
            self.handle_request()
