
from chimera.controllers.console.command import HighLevelCommand, command
from chimera.controllers.console.message import Message, Error

from chimera.controllers.console.controller import ConsoleController
from chimera.controllers.console.commands.object import ObjectCommand

class SiteCommand (HighLevelCommand):

    def __init__ (self):
        HighLevelCommand.__init__ (self, "site", [])

        self._kind  = ["instrument", "controller", "driver"]
        self._kinds = ["instruments", "controllers", "drivers"]

    @command    
    def list (self, args, namespace):

        def insts ():
            return [Message("=== Instruments ==="), ConsoleController().getManager()._instruments.items()]

        def ctrls ():
            return [Message("=== Controllers ==="), ConsoleController().getManager()._controllers.items()]

        def drvs ():
            return [Message("=== Drivers ==="), ConsoleController().getManager()._drivers.items()]

        if not args:
            return insts()+ctrls()+drvs()

        if args[0] == "instruments":
            return insts()
        elif args[0] == "controllers":
            return ctrls()
        elif args[0] == "drivers":
            return drvs()
        else:
            return Error ("invalid object type '%s'" % args[0])

    def complete_list (self, prefix, line, prefix_start, prefix_end):

        "[instruments|controllers|drivers]?"
        
        # only one argument allowed
        if prefix_start > 0:
            return []

        if not prefix:
            return self._kinds
        else:
            return [kind for kind in self._kinds if kind.startswith(prefix)]

    @command
    def add (self, args, namespace):

        if not args or len (args) < 2:
            return Error ("Invalid syntax")

        kind, location = args

        if location in namespace:
            return Error ("%s already on the system." % location)

        ret = False

        if kind == "instrument":
            ret = ConsoleController().getManager().addInstrument (location)
        elif kind == "controller":
            ret = ConsoleController().getManager().addController (location)
        elif kind == "driver":
            ret = ConsoleController().getManager().addDriver (location)
        else:
            return Error("Invalid object type '%s'" % kind)

        if not ret:
            return Error("Couldn't add %s '%s'" % (kind, location))

        # get the object and put on the namespace
        obj = ConsoleController().getObject(location)
        namespace.append (ObjectCommand (location, obj))

        return False

    def complete_add (self, prefix, line, prefix_start, prefix_end):

        "[instrument|controller|driver] /Location/location"

        if prefix_start == 0:
            if not prefix:
                return self._kind
            else:
                return [kind for kind in self._kind if kind.startswith(prefix)]

        return []    

