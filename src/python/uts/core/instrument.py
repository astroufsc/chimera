import uts

from uts.core.proxy import AsyncResult
from uts.core.event import EventsProxy

import time

import threading

### TODO Add life cycle code (start/stop/query/etc)

class InstrumentMeta(type):

	def __new__(metacls, clsname, bases, dictionary):
		
		_evs = []
		for name, obj in dictionary.iteritems():
			if callable(obj) and not name.startswith('__') and hasattr(obj, 'event'):
				_evs.append(name)

		for name in _evs:
			del dictionary[name]

		dictionary['__events__'] = _evs
				
		return super(InstrumentMeta, metacls).__new__(metacls, clsname, bases, dictionary)


class Instrument:

    __metaclass__ = InstrumentMeta

    def __init__(self, name):

        self.name   = name

        self.manager = None
        self.location = None
        self.rpc = None

        self.driver = None

        self.events = EventsProxy(self.__events__)

        # loop control
        self.timeslice = 0.5
        self.looping = False

        # term event
        self.term = threading.Event()

	def __getattr__(self, attr):
		if attr in self.events:
			return self.events.__getattr__(attr)
		else:
			raise AttributeError
		
    def inst_main(self):
        pass

    def main(self):

        # enter main loop
        self._main()
        
        return True

    def _main(self):

        self.looping = True

        try:

            while(self.looping):

                if (self.term.isSet()):
                    self.looping = False
                    return
            
                # run instrument control functions
                self.inst_main()

                time.sleep(self.timeslice)

        except KeyboardInterrupt, e:
            self.looping = False
            return
        
