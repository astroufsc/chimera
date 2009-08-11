
import socket
import threading
import SocketServer
import struct
import math

from chimera.core.chimeraobject import ChimeraObject
from chimera.util.coord import Coord
from chimera.util.position import Position

class GotoMessage:

    def __init__(self, buffer):
        # discard time
        buffer.recv(8)
        self.ra = struct.unpack("<1I", buffer.recv(4))[0]
        self.ra *=  (math.pi/0x80000000)
        self.ra = Coord.fromR(self.ra).toHMS()
        self.dec = struct.unpack("<1i", buffer.recv(4))[0]
        self.dec *= (math.pi/0x80000000)
        self.dec = Coord.fromR(self.dec).toDMS()
        self.position = Position.fromRaDec(self.ra, self.dec)

    def __str__ (self):
        return "<goto> %s"  % self.position

class CurrentPositionMessage:

    def __init__(self, position, error=False):
        status = 0
        if error:
            status = 1
        self.msg = struct.pack("<HHQIii",
                               24, # length
                               0,  # type
                               0,  # time
                               int(math.floor(0.5 + position.ra.R*(0x80000000/math.pi))),  # ra
                               int(math.floor(0.5 + position.dec.R*(0x80000000/math.pi))), # dec
                               status) # status
    def __str__(self):
        return self.msg
        
class StellariumMessageHandler (SocketServer.BaseRequestHandler):

    def handle(self):

        try:
            if self.server.client:
                self.server.client.close()
                
            self.server.client = self.request.makefile("wb")

            buff = self.request.recv(2)
            if len(buff) < 2:
                self.server.client.close()
                self.server.client = None
                return
            
            msg_length = struct.unpack("<1H", buff)[0]
            msg_type = struct.unpack("<1H", self.request.recv(2))[0]

            if msg_type == 0:
                msg = GotoMessage(self.request)
                self.server.controller.receiveGoto(msg)
            else:
                self.server.controller.warning("Unknown message type: %d" % msg_type)
        except Exception, e:
            self.server.controller.log.exception(e)


class StellariumServer (SocketServer.ThreadingMixIn, SocketServer.TCPServer):

    controller = None
    client = None

    allow_reuse_address = True

    def sendPosition (self, position, error=False):
        if self.client:
            try:
                self.controller.log.debug("[stellarium] send current position: %s" % position)
                msg = CurrentPositionMessage(position, error=error)
                self.client.write(str(msg))
                self.client.flush()
            except socket.error, e:
                self.controller.log.exception(e)
                self.client = None

class Stellarium(ChimeraObject):

    __config__ = {"telescope": "/Telescope/0",
                  "position_update_frequency": 2,
                  "hostname": "localhost",
                  "port"    : 9000}
    
    def __init__ (self):
        ChimeraObject.__init__(self)

        self.telescope = None
        self.server = None

        self.error = False

    def __start__ (self):
        self.setHz(self["position_update_frequency"])
        self.telescope = self.getManager().getProxy(self["telescope"])

        self.server = StellariumServer((self["hostname"], self["port"]), StellariumMessageHandler)
        self.server.controller = self
        self.serverThread = threading.Thread(target=self.server.serve_forever)
        self.serverThread.setDaemon(True)
        self.serverThread.setName("stellarium server")
        self.serverThread.start()

    def __stop__ (self):
        self.server.shutdown()
        self.serverThread.join()

    def control (self):
        self.server.sendPosition(self.telescope.getPositionRaDec(), error=self.error)
        self.error = False
        return True

    def receiveGoto(self, message):
        self.log.debug("[stellarium] goto %s" % message.position)
        try:
            self.telescope.slewToRaDec(message.position)
            self.error = False
        except Exception:
            self.error = True
