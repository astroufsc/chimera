
from chimera.controllers.console.command import Command
from chimera.controllers.console.controller import ConsoleController
from chimera.controllers.console.message import Message, Error

class UnaliasCommand (Command):

    def __init__ (self):
        Command.__init__ (self, "unalias")

    def execute (self, args, namespace):

        if not args:
            return Error ("invalid syntax")       
        
        names = None
        results = []
        
        try:
            names = args.strip().split ()
        except ValueError:
            return Error ("invalid syntax")

        for name in names:

            cmd = [cmd for cmd in namespace if name in cmd.aliases()]

            if not cmd:
                results.append(Error ("'%s' it's not defined." % name))
                continue

            cmd = cmd[0]
            cmd.delAlias(name)

        return results

    def longhelp (self):
        return "long long help for unalias"

    def shorthelp (self):
        return "Usage: unalias name"

