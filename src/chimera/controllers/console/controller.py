import sys

from chimera.core.exceptions import ObjectNotFoundException


_global_private_controller_singleton = None

def ConsoleController ():

    global _global_private_controller_singleton

    if not _global_private_controller_singleton:
        _global_private_controller_singleton = _ConsoleControllerSingleton()

    return _global_private_controller_singleton

class _ConsoleControllerSingleton (object):

    def __init__ (self):
        self.controller = None
        self.commander  = None

    def setController (self, controller):
        self.controller = controller

    def setCommander (self, commander):
        self.commander = commander

    def quit (self):
        self.commander.quit(True)

    def getManager(self):
        return self.controller.getManager()

    def getObject (self, name):

        if not self.controller:
            return False

        try:
            obj = self.getManager().getProxy(name)
        except ObjectNotFoundException:
            return False

        return obj
