import os
import signal
import threading

# ============
# FIXME Ugly hacks to python threading works with signal
# FIXME see http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496735
# FIXME see http://greenteapress.com/semaphores/

# FIXME run shutdown on exit
# FIXME log

class Runner (object):

    def __init__ (self, obj):
        self.obj = obj

        self.mainPID = os.getpid()

    
    def main(self):

        # FIXME: shutdown = threading.Event ()

        # from here we will have 2 process. Child process will return from splitAndWatch,
        # while the main process will watch for signals and will kill the child
        # process.
    
        self.splitAndWatch()

        pid = os.getpid ()

        # run obj.init on child process
        if pid != self.mainPID:
            self.obj.init ()


    def splitAndWatch(self):

        child = os.fork()

        if child == 0:
            return

        self.childPID = child

        signal.signal(signal.SIGTERM, self.sighandler)
        signal.signal(signal.SIGINT, self.sighandler)

        try:
            os.wait()
            self.kill()
            
        except OSError:
            pass

    def kill(self):
        os.kill (self.childPID, signal.SIGKILL)

    def sighandler(self, sig, frame):
        self.kill()

