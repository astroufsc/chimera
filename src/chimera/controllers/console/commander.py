#!/usr/bin/env python

import sys
import re
import os
import readline

from cmd import Cmd, IDENTCHARS
from types import ListType, BooleanType, StringType, NoneType, TupleType

from chimera.core.version import _chimera_description_, _chimera_version_

from chimera.controllers.console.controller import ConsoleController
from chimera.controllers.console.namespace  import Namespace
from chimera.controllers.console.message    import Error, Message, Hint
from chimera.controllers.console.command    import Command

from chimera.controllers.console.commands import *

class Commander (Cmd):

    def __init__ (self, controller):
        Cmd.__init__ (self)

        # FIXME: check if this works really
        self.identchars = IDENTCHARS + "/"

        # FIXME: check if this works really
        readline.set_completer_delims(readline.get_completer_delims().replace("/", "#"))

        try:
            readline.read_history_file (os.path.join(os.path.expanduser("~/.chimera_console.history")))
        except IOError:
            pass

        self.intro  = "Welcome to %s - %s\n" % (_chimera_description_, _chimera_version_)
        self.prompt = "chimera> "

        # save our controller and ourself on Chimera singleton
        ConsoleController().setController (controller)
        ConsoleController().setCommander (self)        

        # builtin commands
        self.namespace = Namespace ()

        for command in [name for name in globals() if re.compile("^[A-Za-z]+Command").match (name)]:
            self.namespace.append (globals()[command]())

    def quit (self, from_here=False):

        if from_here:
            ConsoleController().getManager().shutdown()
            return

        print Hint("bye :)")
        readline.write_history_file (os.path.join(os.path.expanduser("~/.chimera_console.history")))


    def do_EOF (self, args):
        self.quit(True)

    def emptyline (self):
        return False

    def default (self, line):
        print Error ("invalid command")
        return False

    def completenames (self, text, *ignored):
        return [name for name in self.namespace.names() if name.startswith(text)]
    
    def _execute (self, cmd, args):

        result = cmd.execute (args, self.namespace)

        if type(result) == BooleanType:
            return result

        if type (result) == NoneType:
            return False

        if type(result) in (ListType, TupleType):
            for msg in result:
                print str(msg)

            return False                

        if type (result) == StringType:
            print result
            return False

        if issubclass (result.__class__, Message):
            print result
            return False

    def _do (self, args):

        name, args = self.lastcmd.split()[0], args

        for cmd in self.namespace:
            if cmd.name() == name or name in cmd.aliases ():
                return self._execute (cmd, args)

        print Error ("Invalid command '%s'" % name)

    def _complete (self, prefix, line, prefix_start, prefix_end):

        name = line.split()[0].strip()

        for cmd in self.namespace:
            
            if not issubclass (cmd.__class__, Command): continue
            
            if cmd.name() == name or name in cmd.aliases ():
                return cmd.complete (prefix, line.strip()[len(name):],
                                     prefix_start - len(name) - 1,
                                     prefix_end   - len(name) - 1)

        return []

    def _help (self):
        print "getting help for %s" % self.lastcmd.split()[1]
        return False

    def __getattr__ (self, attr):

        if   "do_" in attr:
            return self._do
        elif "complete_" in attr:
            return self._complete
        elif  "help_" in attr:
            return self._help
        else:
            raise AttributeError


if __name__ == "__main__":

    console = Commander (None)
    console.cmdloop ()
