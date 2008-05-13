
from chimera.controllers.console.controller import ConsoleController
from chimera.controllers.console.command import Command
from chimera.controllers.console.message import Message, Error

class QuitCommand (Command):

    def __init__ (self):
        Command.__init__ (self, "quit", [])
        
    def execute (self, args, namespace):
        return ConsoleController().quit()
    
