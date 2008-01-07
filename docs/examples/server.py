
import logging
logging.getLogger("chimera").setLevel(logging.INFO)

from chimera.core.manager import Manager

from minimo import Minimo

manager = Manager(host='localhost', port=8000)
manager.addClass(Minimo, "m", config={"option1": "blah blah"}, start=True)
manager.wait()

