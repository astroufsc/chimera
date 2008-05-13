
from chimera.controllers.console.command import Command
from chimera.controllers.console.message import Message, Error

class AliasCommand (Command):

    def __init__ (self):
        Command.__init__ (self, "alias")

    def execute (self, args, namespace):

        if not args:
            return Error ("invalid syntax")
        
        name, value = None, None
        
        try:
            name, value = args.split ()
        except ValueError:
            return Error ("invalid syntax")

        cmd = [cmd for cmd in namespace if cmd.name() == value]

        if not cmd:
            return Error ("'%s' it's not defined." % value)
        else:
            cmd = cmd[0]

        if name in cmd.aliases():
            return Error ("'%s' it's already defined. Unset it first ('unalias %s')." % (value, value))
        else:
            cmd.addAlias(name)
            return False

    def longhelp (self):
        return "long long help for alias"

    def shorthelp (self):
        return "Usage: alias name value"

