import pytest

from chimera.core.manager import Manager
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.proxy import Proxy

from chimera.core.exceptions import (
    InvalidLocationException,
    ObjectNotFoundException,
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

    def setup_method(self):
        self.manager = Manager()

    def teardown_method(self):
        self.manager.shutdown()
        del self.manager

    def test_add_start(self):

        # add by class
        assert self.manager.addClass(Simple, "simple", start=True)

        # already started
        with pytest.raises(InvalidLocationException):
            self.manager.addClass(Simple, "simple")

        with pytest.raises(NotValidChimeraObjectException):
            self.manager.addClass(NotValid, "nonono")
        with pytest.raises(InvalidLocationException):
            self.manager.addClass(Simple, "")

        # by location
        assert self.manager.addLocation(
            "/ManagerHelper/h", path=[os.path.dirname(__file__)]
        )
        with pytest.raises(ClassLoaderException):
            self.manager.addLocation("/What/h")
        with pytest.raises(InvalidLocationException):
            self.manager.addLocation("foo")

        # start with error
        # assert self.manager.addLocation('/ManagerHelperWithError/h', start=False)
        # with pytest.raises(ChimeraObjectException):
        # self.manager.start, '/ManagerHelperWithError/h')

        # start who?
        with pytest.raises(InvalidLocationException):
            self.manager.start("/Who/am/I")

        # exceptional cases
        # __init__
        with pytest.raises(ChimeraObjectException):
            self.manager.addLocation(
                "/ManagerHelperWithInitException/h", [os.path.dirname(__file__)]
            )

        # __start__
        with pytest.raises(ChimeraObjectException):
            self.manager.addLocation(
                "/ManagerHelperWithStartException/h", [os.path.dirname(__file__)]
            )

        # __main__
        # with pytest.raises(ChimeraObjectException):
        # self.manager.addLocation("/ManagerHelperWithMainException/h")

    def test_remove_stop(self):

        assert self.manager.addClass(Simple, "simple")

        # who?
        with pytest.raises(InvalidLocationException):
            self.manager.remove("Simple/what")
        with pytest.raises(InvalidLocationException):
            self.manager.remove("foo")

        # stop who?
        with pytest.raises(InvalidLocationException):
            self.manager.stop("foo")

        # ok
        assert self.manager.remove("/Simple/simple") == True

        # __stop__ error
        assert self.manager.addLocation(
            "/ManagerHelperWithStopException/h", path=[os.path.dirname(__file__)]
        )
        with pytest.raises(ChimeraObjectException):
            self.manager.stop("/ManagerHelperWithStopException/h")

        # another path to stop
        with pytest.raises(ChimeraObjectException):
            self.manager.remove("/ManagerHelperWithStopException/h")

        # by index
        assert self.manager.addClass(Simple, "simple")
        assert self.manager.remove("/Simple/0") == True

    def test_proxy(self):

        assert self.manager.addClass(Simple, "simple")

        # who?
        with pytest.raises(InvalidLocationException):
            self.manager.getProxy("wrong")
        with pytest.raises(InvalidLocationException):
            self.manager.getProxy("Simple/simple")

        # ok
        assert self.manager.getProxy("/Simple/simple")
        assert self.manager.getProxy("/Simple/0")

        # calling
        p = self.manager.getProxy("/Simple/0")
        assert isinstance(p, Proxy)

        # # assert p.answer() == 42

        # # oops
        # with pytest.raises(AttributeError):
        #     p.wrong()

    def test_manager(self):

        assert self.manager.addClass(Simple, "simple")

        p = self.manager.getProxy("/Simple/simple")
        assert p

        # m = p.getManager()
        # assert m.GUID() == self.manager.GUID()
