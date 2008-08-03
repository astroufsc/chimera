from chimera.controllers.scheduler.controller import Controller


#import sys
#
#import Pyro.util
#
#def hook (e,v,t):
#    print ''.join(Pyro.util.getPyroTraceback(v))
##sys.excepthook =lambda exctype, value, traceback: Pyro.util.getPyroTraceback(value)
#sys.excepthook = hook
##sys.excepthook()
#
##This class is just here for naming purposes; all work is done by 
##the Controller class in controller.py.
class Scheduler(Controller):
    pass
