import os.path

import pytest

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import (
    ChimeraObjectException,
    ClassLoaderException,
    NotValidChimeraObjectException,
    ObjectNotFoundException,
)
from chimera.core.proxy import Proxy


class Simple(ChimeraObject):
    def __init__(self):
        ChimeraObject.__init__(self)

    def answer(self):
        return 42


class NotValid:
    pass


class TestManager:
    def test_add_start(self, manager):
        # add by class
        assert manager.add_class(Simple, "simple", start=True)

        # already started
        with pytest.raises(ValueError):
            manager.add_class(Simple, "simple")

        with pytest.raises(NotValidChimeraObjectException):
            manager.add_class(NotValid, "nonono")
        with pytest.raises(ValueError):
            manager.add_class(Simple, "")

        # by location
        assert manager.add_location(
            "/ManagerHelper/h", path=[os.path.dirname(__file__)]
        )
        with pytest.raises(ClassLoaderException):
            manager.add_location("/What/h")
        with pytest.raises(ValueError):
            manager.add_location("foo")

        # start with error
        # assert manager.add_location('/ManagerHelperWithError/h', start=False)
        # with pytest.raises(ChimeraObjectException):
        # manager.start, '/ManagerHelperWithError/h')

        # start who?
        with pytest.raises(ValueError):
            manager.start("/Who/am/I")
        with pytest.raises(ObjectNotFoundException):
            manager.start("/Who/ami")

        # exceptional cases
        # __init__
        with pytest.raises(ChimeraObjectException):
            manager.add_location(
                "/ManagerHelperWithInitException/h", path=[os.path.dirname(__file__)]
            )

        # __start__
        with pytest.raises(ChimeraObjectException):
            manager.add_location(
                "/ManagerHelperWithStartException/h", path=[os.path.dirname(__file__)]
            )

        # __main__
        # with pytest.raises(ChimeraObjectException):
        # manager.add_location("/ManagerHelperWithMainException/h")

    def test_remove_stop(self, manager):
        assert manager.add_class(Simple, "simple")

        # who? (malformed locations raise ValueError, well-formed but
        # unknown ones raise ObjectNotFoundException)
        with pytest.raises(ValueError):
            manager.remove("Simple/what")
        with pytest.raises(ValueError):
            manager.remove("foo")
        with pytest.raises(ObjectNotFoundException):
            manager.remove("/Simple/what")

        # stop who?
        with pytest.raises(ValueError):
            manager.stop("foo")
        with pytest.raises(ObjectNotFoundException):
            manager.stop("/Simple/what")

        # ok
        assert manager.remove("/Simple/simple") is True

        # __stop__ error
        assert manager.add_location(
            "/ManagerHelperWithStopException/h", path=[os.path.dirname(__file__)]
        )
        with pytest.raises(ChimeraObjectException):
            manager.stop("/ManagerHelperWithStopException/h")

        # another path to stop
        with pytest.raises(ChimeraObjectException):
            manager.remove("/ManagerHelperWithStopException/h")

        # by index
        assert manager.add_class(Simple, "simple")
        assert manager.remove("/Simple/0") is True

    def test_proxy(self, manager):
        assert manager.add_class(Simple, "simple")

        # who?
        with pytest.raises(ValueError):
            manager.get_proxy("wrong")
        with pytest.raises(ValueError):
            manager.get_proxy("Simple/simple")

        # ok
        assert manager.get_proxy("/Simple/simple")
        assert manager.get_proxy("/Simple/0")

        # calling
        p = manager.get_proxy("/Simple/0")
        assert isinstance(p, Proxy)

        assert p.answer() == 42

    def test_manager(self, manager):
        assert manager.add_class(Simple, "simple")

        p = manager.get_proxy("/Simple/simple")
        assert p

        # m = p.get_manager()
        # assert m.GUID() == manager.GUID()
