from chimera.core.location import Location

class ImageURI(Location):
    def __init__(self, imageServer, hash):
#        self._host = imageServer.getManager().getHostname()
#        self._port = imageServer.getManager().getPort()
        isL = imageServer.getLocation()
#        self._cls = isL.cls
#        self._name = isL.name
#        self.config = {'hash':hash}
        Location.__init__(self, cls=isL.cls, name=isL.name, host = imageServer.getManager().getHostname(), port = imageServer.getManager().getPort(), config={'hash':hash})
    
    def __str__(self):
        return Location.__str__(self) + ('?hash=%s' % str(self.config['hash']))