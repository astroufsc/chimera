import uts

from uts.interfaces.lifecycle import ILifeCycle
from uts.core.event import EventsProxy

import time
import threading

class BasicLifeCycle(ILifeCycle):

    def __init__(self, manager):

        self.manager = manager

        # loop control
        self.timeslice = 0.5
        self.looping = False

        # term event
        self.term = threading.Event()

        # event handling
        self.__eventsProxy__ = EventsProxy(self.__events__)

    # TODO: driver loading
    
    def init(self):
        pass

    def shutdown(self):
        pass

    def main(self):
            
        # FIXME: better main loop control
        
        # enter main loop
        self._main()
        
        return True

    def control(self):
        pass

    def _main(self):

        self.looping = True

        try:

            while(self.looping):

                if (self.term.isSet()):
                    self.looping = False
                    return
            
                # run control function
                self.control()

                time.sleep(self.timeslice)

        except KeyboardInterrupt, e:
            self.looping = False
            return

    def __getattr__(self, attr):
        if attr in self.__eventsProxy__:
            return self.__eventsProxy__[attr]
        else:
            raise AttributeError
        
        
