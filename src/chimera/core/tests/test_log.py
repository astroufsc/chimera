
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.manager       import Manager
from chimera.core.exceptions    import ChimeraException

from nose.tools import assert_raises

import chimera.core.log
import logging

log = logging.getLogger("chimera.test_log")

class TestLog (object):

    def test_log (self):

        class Simple (ChimeraObject):
            def __init__ (self):
                ChimeraObject.__init__(self)

            def answer (self):
                try:
                    raise ChimeraException("I'm an Exception, sorry.")
                except ChimeraException:
                    self.log.exception("from except: wow, exception caught.")
                    raise ChimeraException("I'm a new Exception, sorry again")

        manager = Manager()
        manager.addClass(Simple, "simple")

        simple = manager.getProxy(Simple)

        try:
            simple.answer()
        except ChimeraException, e:
            assert e.cause != None
            log.exception("wow, something wrong")

        manager.shutdown()

        
