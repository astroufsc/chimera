import xmlrpclib

from uts.core.lifecycle import BasicLifeCycle

class RemoteClient(BasicLifeCycle):

    __options__ = {"host": "150.16.3047",
                   "port": 1090}

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

        self.proxy = None

    def init(self, config):
        
        self.config += config

        url = "http://%s:%d/RPC2" % (self.config.host, self.config.port)

        self.proxy = xmlrpclib.ServerProxy(url)
        # test!

    def __getattr__ (self, attr):

        print "aqui"

        return self.proxy.__getattr__ (attr)
