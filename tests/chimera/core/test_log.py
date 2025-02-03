from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ChimeraException

import logging

log = logging.getLogger("chimera.test_log")


class TestLog(object):

    def test_log(self, manager):

        class Simple(ChimeraObject):
            def __init__(self):
                ChimeraObject.__init__(self)

            def answer(self):
                try:
                    raise ChimeraException("I'm an Exception, sorry.")
                except ChimeraException:
                    self.log.exception("from except: wow, exception caught.")
                    raise ChimeraException("I'm a new Exception, sorry again")

        manager.addClass(Simple, "simple")

        simple = manager.getProxy("/Simple/simple")

        try:
            simple.answer()
        except ChimeraException as e:
            assert e.cause is not None
            log.exception("wow, something wrong")
