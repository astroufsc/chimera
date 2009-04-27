import threading
import select
import SocketServer
import socket

from chimera.core.exceptions import ChimeraException
from chimera.core.constants import MANAGER_BEACON_PORT, MANAGER_BEACON_CHALLENGE, MANAGER_BEACON_ERROR


class _ManagerBeaconHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request[0]
        sk = self.request[1]

        if data == MANAGER_BEACON_CHALLENGE:
            sk.sendto("%s:%s" % (self.server.manager.getHostname(), self.server.manager.getPort()), self.client_address)
        else:
            sk.sendto(MANAGER_BEACON_ERROR, self.client_address)
        
class ManagerBeacon(SocketServer.ThreadingUDPServer):

    def __init__ (self, manager):

        SocketServer.UDPServer.allow_reuse_address = True
        SocketServer.ThreadingUDPServer.daemon_threads = True

        try:
            SocketServer.ThreadingUDPServer.__init__(self, ("", MANAGER_BEACON_PORT), _ManagerBeaconHandler)
            # hack! there is no interface to do that right!
            #self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1) 
        except Exception, e:
            raise ChimeraException("Failed to start Manager Beacon.")

        self.manager = manager
        self.shouldDie = threading.Event()

    def shutdown(self):
        self.shouldDie.set()

    def get_request (self):

        ret = select.select([self.fileno()], [], [self.fileno()], 0)
        if self.fileno() in ret[0]:
            data, client_addr = self.socket.recvfrom(self.max_packet_size)
            return (data, self.socket), client_addr
        else:
            return (None, None)
        
    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
        if request:
            self.RequestHandlerClass(request, client_address, self)

    def run(self):
        while not self.shouldDie.isSet():
            self.handle_request()

        
