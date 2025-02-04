import pytest

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.proxy import Proxy

from chimera.core.exceptions import (
    InvalidLocationException,
    NotValidChimeraObjectException,
    ChimeraObjectException,
    ClassLoaderException,
)

import os.path


class Simple(ChimeraObject):

    def __init__(self):
        ChimeraObject.__init__(self)

    def answer(self):
        return 42


class NotValid(object):
    pass


class TestManager(object):

    def test_add_start(self, manager):

        # add by class
        assert manager.addClass(Simple, "simple", start=True)

        # already started
        with pytest.raises(InvalidLocationException):
            manager.addClass(Simple, "simple")

        with pytest.raises(NotValidChimeraObjectException):
            manager.addClass(NotValid, "nonono")
        with pytest.raises(InvalidLocationException):
            manager.addClass(Simple, "")

        # by location
        assert manager.addLocation("/ManagerHelper/h", path=[os.path.dirname(__file__)])
        with pytest.raises(ClassLoaderException):
            manager.addLocation("/What/h")
        with pytest.raises(InvalidLocationException):
            manager.addLocation("foo")

        # start with error
        # assert manager.addLocation('/ManagerHelperWithError/h', start=False)
        # with pytest.raises(ChimeraObjectException):
        # manager.start, '/ManagerHelperWithError/h')

        # start who?
        with pytest.raises(InvalidLocationException):
            manager.start("/Who/am/I")

        # exceptional cases
        # __init__
        with pytest.raises(ChimeraObjectException):
            manager.addLocation(
                "/ManagerHelperWithInitException/h", [os.path.dirname(__file__)]
            )

        # __start__
        with pytest.raises(ChimeraObjectException):
            manager.addLocation(
                "/ManagerHelperWithStartException/h", [os.path.dirname(__file__)]
            )

        # __main__
        # with pytest.raises(ChimeraObjectException):
        # manager.addLocation("/ManagerHelperWithMainException/h")

    def test_remove_stop(self, manager):

        assert manager.addClass(Simple, "simple")

        # who?
        with pytest.raises(InvalidLocationException):
            manager.remove("Simple/what")
        with pytest.raises(InvalidLocationException):
            manager.remove("foo")

        # stop who?
        with pytest.raises(InvalidLocationException):
            manager.stop("foo")

        # ok
        assert manager.remove("/Simple/simple") is True

        # __stop__ error
        assert manager.addLocation(
            "/ManagerHelperWithStopException/h", path=[os.path.dirname(__file__)]
        )
        with pytest.raises(ChimeraObjectException):
            manager.stop("/ManagerHelperWithStopException/h")

        # another path to stop
        with pytest.raises(ChimeraObjectException):
            manager.remove("/ManagerHelperWithStopException/h")

        # by index
        assert manager.addClass(Simple, "simple")
        assert manager.remove("/Simple/0") is True

    def test_proxy(self, manager):

        assert manager.addClass(Simple, "simple")

        # who?
        with pytest.raises(InvalidLocationException):
            manager.getProxy("wrong")
        with pytest.raises(InvalidLocationException):
            manager.getProxy("Simple/simple")

        # ok
        assert manager.getProxy("/Simple/simple")
        assert manager.getProxy("/Simple/0")

        # calling
        p = manager.getProxy("/Simple/0")
        assert isinstance(p, Proxy)

        # # assert p.answer() == 42

        # # oops
        # with pytest.raises(AttributeError):
        #     p.wrong()

    def test_manager(self, manager):

        assert manager.addClass(Simple, "simple")

        p = manager.getProxy("/Simple/simple")
        assert p

        # m = p.getManager()
        # assert m.GUID() == manager.GUID()
