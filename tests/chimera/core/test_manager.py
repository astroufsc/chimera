import logging
import os.path
import time

import pytest

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import (
    ChimeraObjectException,
    ClassLoaderException,
    InvalidLocationException,
    NotValidChimeraObjectException,
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
        with pytest.raises(InvalidLocationException):
            manager.add_class(Simple, "simple")

        with pytest.raises(NotValidChimeraObjectException):
            manager.add_class(NotValid, "nonono")
        with pytest.raises(InvalidLocationException):
            manager.add_class(Simple, "")

        # by location
        assert manager.add_location(
            "/ManagerHelper/h", path=[os.path.dirname(__file__)]
        )
        with pytest.raises(ClassLoaderException):
            manager.add_location("/What/h")
        with pytest.raises(InvalidLocationException):
            manager.add_location("foo")

        # start with error
        # assert manager.add_location('/ManagerHelperWithError/h', start=False)
        # with pytest.raises(ChimeraObjectException):
        # manager.start, '/ManagerHelperWithError/h')

        # start who?
        with pytest.raises(InvalidLocationException):
            manager.start("/Who/am/I")

        # exceptional cases
        # __init__
        with pytest.raises(ChimeraObjectException):
            manager.add_location(
                "/ManagerHelperWithInitException/h", [os.path.dirname(__file__)]
            )

        # __start__
        with pytest.raises(ChimeraObjectException):
            manager.add_location(
                "/ManagerHelperWithStartException/h", [os.path.dirname(__file__)]
            )

        # __main__
        # with pytest.raises(ChimeraObjectException):
        # manager.add_location("/ManagerHelperWithMainException/h")

    def test_remove_stop(self, manager):
        assert manager.add_class(Simple, "simple")

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
        with pytest.raises(InvalidLocationException):
            manager.get_proxy("wrong")
        with pytest.raises(InvalidLocationException):
            manager.get_proxy("Simple/simple")

        # ok
        assert manager.get_proxy("/Simple/simple")
        assert manager.get_proxy("/Simple/0")

        # calling
        p = manager.get_proxy("/Simple/0")
        assert isinstance(p, Proxy)

        # # assert p.answer() == 42

        # # oops
        # with pytest.raises(AttributeError):
        #     p.wrong()

    def test_stop_joins_control_loop(self, manager):
        class Looper(ChimeraObject):
            def control(self):
                time.sleep(0.05)
                return True

        manager.add_class(Looper, "looper", start=True)
        resource = manager.resources.get("/Looper/looper")

        deadline = time.monotonic() + 5
        while getattr(resource.instance, "__loop_native_id__", None) is None:
            assert time.monotonic() < deadline, "loop never started"
            time.sleep(0.01)

        loop_future = resource.loop
        manager.stop("/Looper/looper")

        # __stop__ must not race a still-executing control()
        assert loop_future.done(), "stop() returned before the loop finished"
        assert resource.loop is None

    def test_control_loop_exception_is_logged(self, manager):
        class Bomb(ChimeraObject):
            def control(self):
                raise RuntimeError("boom")

        records: list[logging.LogRecord] = []

        class Capture(logging.Handler):
            def emit(self, record: logging.LogRecord):
                records.append(record)

        handler = Capture()
        manager_logger = logging.getLogger("chimera.core.manager")
        manager_logger.addHandler(handler)
        try:
            manager.add_class(Bomb, "bomb", start=True)

            deadline = time.monotonic() + 5
            while not any("control loop died" in r.getMessage() for r in records):
                assert time.monotonic() < deadline, "loop death never logged"
                time.sleep(0.01)
        finally:
            manager_logger.removeHandler(handler)

    def test_manager(self, manager):
        assert manager.add_class(Simple, "simple")

        p = manager.get_proxy("/Simple/simple")
        assert p

        # m = p.get_manager()
        # assert m.GUID() == manager.GUID()
