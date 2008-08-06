from chimera.core.location import Location
from chimera.core.manager import Manager
from chimera.core.exceptions import ObjectNotFoundException
#from chimera.controllers.imageserver.imageserver import ImageServer

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
    
    def getProxy(self):
        m = Manager.getManagerProxy()
        try:
            imageServer = m.getProxy(self)
        except ObjectNotFoundException:
            #TODO: What if imageserver isn't running? how to start it?
            #imageServer = m.addClass(ImageServer, self.name)
            raise
        return imageServer.getProxyByURI(self)
