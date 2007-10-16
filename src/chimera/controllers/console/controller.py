import sys

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
        self.commander.quit ()
        return True

    def getManager(self):
        return self.controller.manager

    def getObject (self, name):

        if not self.controller:
            return False

        obj = None

        if not obj:
            obj = self.controller.manager.getInstrument (name, proxy=False)

        if not obj:
            obj = self.controller.manager.getController (name, proxy=False)

        if not obj:
            obj = self.controller.manager.getDriver (name, proxy=False)

        return obj
