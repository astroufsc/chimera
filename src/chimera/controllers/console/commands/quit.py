
from chimera.controllers.console.command import Command
from chimera.controllers.console.message import Message, Error

from chimera.controllers.console.controller import ConsoleController

class QuitCommand (Command):

    def __init__ (self):
        Command.__init__ (self, "quit", [])
        
    def execute (self, args, namespace):
        return ConsoleController().quit()
    
