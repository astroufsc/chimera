from SimpleXMLRPCServer import SimpleXMLRPCServer

from uts.core.lifecycle import BasicLifeCycle

class RemoteServer(BasicLifeCycle):

    __options__ = {"host": "150.16.3047",
                   "port": 1090,
                   "driver": "/Fake/camera"}

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

        self.srv = None
        self.obj = None

    def init(self, config):

        self.config += config

        self.obj = self.manager.getDriver (self.config.driver)

        self.srv = SimpleXMLRPCServer ((self.config.host, self.config.port))
        self.srv.register_introspection_functions ()
        self.srv.register_instance (self.obj)

    def control (self):

        self.srv.serve_forever ()


