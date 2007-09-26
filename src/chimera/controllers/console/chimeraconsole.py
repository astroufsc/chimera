#!/usr/bin/env python

import sys
from cmd import Cmd
from types import ListType, StringType

from chimera.core.version import _chimera_description_, _chimera_version_
from chimera.core.lifecycle import BasicLifeCycle
from chimera.core.config import OptionConversionException

from chimera.util.output import red

"""
Use cases:

object administrative stuff
======

site list [instruments|drivers|controllers]

site add [instrument|driver|controller] /Lah/lah using config.xml
site add [instrument|driver|controller] /Lah/lah using var1=1,var2=2,...,varn=n

site remove [instrument|driver|controller] /Location/lah

object manipulation
======

set tel /Telescope/name

# operation
in: tel slewToRaDec '00 00 00' '00 00 00'
out: True
err: Too low.

tel slewToRaDec '00 00 00' '00 00 00'

# automatic getters/setters if available
tel ra
tel dec

tel maxSlewRate 100

# configuration
tel config var1=value1,var2=value2

in: tel config var1,var2
out: var1=value1
out: var2=value2

in: tel config
out:
var1: value1
var2: value2

unset tel
"""

class Command (object):

    def __init__ (self, name = None, aliases = None):
        self._name = name or ""
        self._aliases = aliases or []

    def name (self):
        return self._name

    def aliases (self):
        return self._aliases

    def execute (self, args, namespace):
        return False

    def complete (self, prefix, line, prefix_start, prefix_end):
        return []

    def longhelp (self):
        return ""

    def shorthelp (self):
        return ""

class ObjectCommand (Command):

    def __init__ (self, name, obj):
        Command.__init__ (self, name)

        self.obj = obj
        
        self.specials = {"config": self._configHandler}
        
    def execute (self, args, namespace):

        if not args:
            return False

        method = args.split()[0]

        if method in self.specials:
            return self.specials[method] (args)

        return self._methodHandler (method, args.split()[1:] or [])

    def _methodHandler (self, method, args):
        return "%s %s" % (method, args)

    def _configHandler (self, args):

        if not hasattr (self.obj, 'config'):
            return Error ("Object doesn't support configuration")

        args = args[len("config"):].strip()

        if not args:
            # return all
            return Message (self.obj.config.items())

        def getConfig (key):
            return self.obj.config[key]

        def setConfig (key, value):
            self.obj.config[key] = value
            return None

        # parse required on config args
        tasks   = []
        errors  = []
        results = []

        for item in args.split(","):

            if "=" in item:
                # setter one
                try:
                    key, value = item.split("=")
                    key = key.strip()
                    value = value.strip()

                    try:
                        value = eval(value)
                    except Exception:
                        errors.append ("invalid configuration value")    

                    tasks.append ((setConfig, (key, value)))
                    
                except ValueError:
                    errors.append ("invalid syntax")

            else:
                # simple getters
                key = item.strip()

                if not key:
                    continue
                
                tasks.append ((getConfig, (key,)))

        for task in tasks:

            handler, name, args = task[0], task[1][0], task[1]
            
            try:
                result = handler (*args)
                results.append ((name, result))
            except KeyError:
                errors.append ("'%s' doesn't exists" % name)
            except OptionConversionException:
                errors.append ("invalid configuration value to '%s'" % name)

        errors_list  = [ Error("%s: %s" % (self.name(), err)) for err in errors ]
        results_list = [ Message("%s: %s" % res) for res in results if res[1] != None ]

        return errors_list + results_list


class SetKeyword (Command):

    def __init__ (self):
        Command.__init__ (self, "set")

    def execute (self, args, namespace):

        if not args:
            return False
        
        name, value = None, None
        
        try:
            name, value = args.split ()

            if name not in namespace:
                obj = Site().getObject(value)

                if not obj:
                    return Error ("Cannot found %s" % value)
                
                namespace.append (ObjectCommand (name, obj))

            else:
                return Error ("'%s' already defined. Unset it first ('unset %s')." % (name, name))

        except ValueError:
            return Error ("invalid syntax")

    def longhelp (self):
        return "long long help for set"

    def shorthelp (self):
        return "Usage: set name value"


def command (method):
    method.__command__ = True
    return method

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
            pass

        return Error("Invalid option '%s' to '%s'" % (cmd, self.name()))


class SiteCommand (HighLevelCommand):

    def __init__ (self):
        HighLevelCommand.__init__ (self, "site", ['s'])

        self._kind  = ["instrument", "controller", "driver"]
        self._kinds = ["instruments", "controllers", "drivers"]

    @command    
    def list (self, args, namespace):

        def insts ():
            return [Message("=== Instruments ==="), Site().getManager()._instruments.items()]

        def ctrls ():
            return [Message("=== Controllers ==="), Site().getManager()._controllers.items()]

        def drvs ():
            return [Message("=== Drivers ==="), Site().getManager()._drivers.items()]

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

        ret = False

        if kind == "instrument":
            ret = Site().getManager().addInstrument (location)
        elif kind == "controller":
            ret = Site().getManager().addController (location)
        elif kind == "driver":
            ret = Site().getManager().addDriver (location)
        else:
            return Error("Invalid object type '%s'" % kind)

        if not ret:
            return Error("Couldn't add %s '%s'" % (kind, location))

        return False

    def complete_add (self, prefix, line, prefix_start, prefix_end):

        "[instrument|controller|driver] /Location/location"

        if prefix_start == 0:
            if not prefix:
                return self._kind
            else:
                return [kind for kind in self._kind if kind.startswith(prefix)]

        return []    


_global_private_site_singleton = None

def Site ():

    global _global_private_site_singleton

    if not _global_private_site_singleton:
        _global_private_site_singleton = _SiteSingleton()

    return _global_private_site_singleton

class _SiteSingleton (object):

    def __init__ (self):
        self.controller = None

    def setController (self, controller):
        self.controller = controller

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

class Namespace (list):

    def __init__ (self):
        list.__init__ (self)

    def __contains__ (self, name):

        for cmd in self:
            if cmd.name () == name or name in cmd.aliases():
                return True

        return False

    def names (self):
        names = [cmd.name() for cmd in self]

        for cmd in self:
            names += cmd.aliases()

        return names    

class Message (object):

    def __init__ (self, msg = None):
        self.msg = msg or ""

    def __str__ (self):
        return str(self.msg)

class Error (Message):

    def __init__ (self, msg):
        Message.__init__ (self, msg)

    def __str__ (self):
        return red (str(self.msg))
    
class ChimeraConsoleCommander (Cmd):

    def __init__ (self, controller):
        Cmd.__init__ (self)

        self.intro  = "Welcome to %s - %s\n" % (_chimera_description_, _chimera_version_)
        self.prompt = "chimera> "

        # save our controller on Site singleton
        Site().setController (controller)

        # builtin commands
        self.namespace = Namespace ()
        self.namespace.append (SetKeyword())
        self.namespace.append (SiteCommand())

    def do_EOF (self, args):
        print "Bye..."
        return True

    def emptyline (self):
        return False

    def _msg (self, buff, msg):
        buff.write(msg)
        buff.flush()
        
    def _error (self, msg):
        self._msg (sys.stderr, red(msg))

    def _result (self, msg):
        self._msg (sys.stdout, msg)

    def _execute (self, cmd, args):

        # NOTE: we always return False because of Cmd rules.
        # NOTE: False means get another command, True means quit command loop

        result = cmd.execute (args, self.namespace)

        if not result:
            return False

        if type(result) == ListType:
            for msg in result:
                print msg
        else:
            print result

        return False

    def _do (self, args):

        name, args = self.lastcmd.split()[0], args

        for cmd in self.namespace:
            if cmd.name() == name or name in cmd.aliases ():
                return self._execute (cmd, args)

        self._error ("Invalid command '%s'\n" % name)

    def _complete (self, prefix, line, prefix_start, prefix_end):

        name = line.split()[0].strip()

        for cmd in self.namespace:
            if cmd.name() == name or name in cmd.aliases ():
                return cmd.complete (prefix, line.strip()[len(name):],
                                     prefix_start - len(name) - 1,
                                     prefix_end   - len(name) - 1)

        return []

    def _help (self):
        print "getting help for %s" % self.lastcmd.split()[1]
        return False

    def completenames (self, text, *ignored):
        return [name for name in self.namespace.names() if name.startswith(text)]
    
    def __getattr__ (self, attr):

        if   "do_" in attr:
            return self._do
        elif "complete_" in attr:
            return self._complete
        elif  "help_" in attr:
            return self._help
        else:
            raise AttributeError


class ChimeraConsole (BasicLifeCycle):

    def __init__ (self, manager):
        BasicLifeCycle.__init__(self, manager)

        self.console = None

    def init(self, config):
        self.config += config
        
        self.console = ChimeraConsoleCommander (self)
        return True

    def main (self):

        try:
            self.console.cmdloop ()
        except KeyboardInterrupt:
            print "Ctrl+C... bye"
            sys.exit (1)

if __name__ == "__main__":

    console = ChimeraConsoleCommander (None)
    console.cmdloop ()
