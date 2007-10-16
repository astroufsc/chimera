
from chimera.controllers.console.message import Message, Error

def command (method):
    method.__command__ = True
    return method

class Command (object):

    def __init__ (self, name = None, aliases = None):
        self._name = name or ""
        self._aliases = aliases or []

    def name (self):
        return self._name

    def aliases (self):
        return self._aliases

    def addAlias (self, alias):
        if alias not in self._aliases:
            return self._aliases.append (alias)

        return False

    def delAlias (self, alias):
        if alias not in self._aliases:
            return False

        return self._aliases.remove(alias)

    def execute (self, args, namespace):
        return False

    def complete (self, prefix, line, prefix_start, prefix_end):
        return []

    def longhelp (self):
        return ""

    def shorthelp (self):
        return ""

class HighLevelCommand (Command):

    def __init__ (self, name, aliases = []):
        Command.__init__ (self, name, aliases)

        self._cmds = None
        self._completers = None

    def _getCommands(self):

        if self._cmds:
            return self._cmds

        self._cmds = {}

        for name in dir (self):
            attr = getattr (self, name)

            if callable(attr) and hasattr(attr, "__command__"):
                self._cmds[name] = attr

        return self._cmds

    def _getCompleters (self):

        if self._completers:
            return self._completers

        self._completers = {}

        for cmd in self._getCommands ():
            completer_name = 'complete_%s' % cmd

            if hasattr(self, completer_name):
                attr = getattr(self, completer_name)

                if callable(attr):
                    self._completers[cmd] = getattr(self, completer_name)

        return self._completers

    def complete (self, prefix, line, prefix_start, prefix_end):

        if not line.strip():
            return self._getCommands().keys()
        else:
            # subcommand prefix
            if prefix_start == 0:
                return [cmd for cmd in self._getCommands() if cmd.startswith(prefix) ]
            else:
                # subcommand arguments
                subcommand_name = line.strip().split()[0]

                if subcommand_name in self._getCompleters():
                    return self._getCompleters()[subcommand_name] (prefix, line.strip()[len(subcommand_name):],
                                                                   prefix_start - len(subcommand_name) - 1,
                                                                   prefix_end   - len(subcommand_name) - 1)
                
        return []
    
    def execute (self, args, namespace):

        if not args:
            return False

        try:
            splitted = args.split()

            if len (splitted) > 1:
                cmd, args = splitted[0], splitted[1:]
            else:
                cmd, args = splitted[0], []

            # try to found a handler
            if cmd in self._getCommands ():
                handler = getattr (self, '%s' % cmd)
                return handler (args, namespace)
            else:
                return Error("Invalid option '%s' to '%s'" % (cmd, self.name()))
            
        except ValueError:
            return Error("Invalid option '%s' to '%s'" % (cmd, self.name()))

        return Error("Invalid option '%s' to '%s'" % (cmd, self.name()))

