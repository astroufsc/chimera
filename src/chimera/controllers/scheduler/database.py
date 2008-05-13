from chimera.controllers.scheduler.model import *

class Database (object):

    """
    Database contains a whole set of programs with observations.

    It run the schedule algorithm and see what the next task to be
    done, then schedule a Machine wakeup using Timer class.

    Machine will ask for the current task and Database will setup a
    new Timer for the next task and so on.
    """

    def __init__ (self):
        self.scheduler = None
        self.machine   = None

    def getTask(self, now):
        """
        Return all tasks that could be done now task that can be done 'now'.
        """
        return N

    def taskDone (self, task):
        pass




