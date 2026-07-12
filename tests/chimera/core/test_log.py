import logging

import pytest

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ChimeraException

log = logging.getLogger("chimera.test_log")


class Simple(ChimeraObject):
    def __init__(self):
        ChimeraObject.__init__(self)

    def answer(self):
        try:
            raise ChimeraException("I'm an Exception, sorry.")
        except ChimeraException:
            self.log.exception("from except: wow, exception caught.")
            raise ChimeraException("I'm a new Exception, sorry again")


class TestLog:
    def test_log(self, manager):
        manager.add_class(Simple, "simple")

        simple = manager.get_proxy("/Simple/simple")
        print("root", log.root)

        # remote exceptions are re-raised by the proxy as a plain Exception
        # carrying the remote error message and traceback
        with pytest.raises(Exception, match="I'm a new Exception, sorry again"):
            simple.answer()

    # def test_log_custom(self, manager):
    #     manager.add_class(Simple, "simple")

    #     simple = manager.get_proxy("/Simple/simple")

    #     try:
    #         simple.answer()
    #     except ChimeraException as e:
    #         assert e.cause is not None
    #         log.exception("wow, something wrong")
