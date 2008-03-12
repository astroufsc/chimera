
import logging
logging.getLogger("chimera").setLevel(logging.WARNING)

from chimera.core.manager       import Manager
from chimera.core.callback      import callback
from chimera.core.exceptions    import printException

from minimo import Minimo, MinimoException

manager = Manager()

m = manager.getProxy(Minimo, "m", host='localhost', port=8000)

# method
print m.doMethod("bar")

# event

@callback(manager)
def doEventClbk (result):
    print result

m.eventDone += doEventClbk
m.doEvent()

# exception
try:
    m.doRaise()
except MinimoException, e:
    printException(e)

# static method
print m.doStatic()

# class method
print m.doClass()

# configuration
print "option1 =>", m['option1']
print "option2 =>", m['option2']

m += {"option1": "new value 1",
      "option2": "new value 2"}

print "option1 =>", m['option1']
print "option2 =>", m['option2']

# bye
manager.shutdown()
