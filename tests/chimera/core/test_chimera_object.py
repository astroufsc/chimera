import pytest

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.methodwrapper import MethodWrapper
from chimera.core.event import event
from chimera.core.state import State
from chimera.core.config import OptionConversionException
from chimera.core.exceptions import InvalidLocationException
from chimera.core.constants import CONFIG_ATTRIBUTE_NAME


class TestChimeraObject(object):

    # FIXME: use fixtures to put each test on their own method (unit tests in small units!)
    def test_class_creation(self):

        # 1. simple class (no inheritance)
        class BaseClass(ChimeraObject):

            __config__ = {"base_config": True}

            @event
            def base_event(self):
                pass

            def base_method(self):
                pass

            def _base_private_method(self):
                pass

        # NOTE: we don't use getattr to avoid descriptor protocol,
        #       which will bind the method when we call getattr

        assert isinstance(BaseClass.__dict__["base_method"], MethodWrapper)
        assert isinstance(BaseClass.__dict__["base_event"], MethodWrapper)

        assert not isinstance(BaseClass.__dict__["_base_private_method"], MethodWrapper)

        assert BaseClass.__dict__[CONFIG_ATTRIBUTE_NAME]["base_config"] is True

        # 2. single inheritance
        class SingleClass(BaseClass):

            __config__ = {"single_config": True}

            @event
            def single_event(self):
                pass

            def single_method(self):
                pass

        assert isinstance(
            SingleClass.__bases__[0].__dict__["base_method"], MethodWrapper
        )
        assert isinstance(SingleClass.__dict__["single_method"], MethodWrapper)
        assert isinstance(SingleClass.__dict__["single_event"], MethodWrapper)

        assert not isinstance(
            SingleClass.__bases__[0].__dict__["_base_private_method"], MethodWrapper
        )

        assert SingleClass.__dict__[CONFIG_ATTRIBUTE_NAME]["base_config"] is True
        assert SingleClass.__dict__[CONFIG_ATTRIBUTE_NAME]["single_config"] is True

        # 3. multiple inheritance
        class AnotherBase(ChimeraObject):
            __config__ = {"another_base_config": True}

            def another_base_method(self):
                pass

        class NonChimeraClass(object):
            __config__ = {}

            def non_chimera_method(self):
                pass

        class MultipleClass(SingleClass, AnotherBase, NonChimeraClass):
            __config__ = {"multiple_config": True, "base_config": "overridden"}

            def multiple_method(self):
                pass

        assert isinstance(MultipleClass.__dict__["multiple_method"], MethodWrapper)
        assert isinstance(
            MultipleClass.__bases__[0].__dict__["single_method"], MethodWrapper
        )
        assert isinstance(
            MultipleClass.__bases__[1].__dict__["another_base_method"], MethodWrapper
        )

        assert not isinstance(
            MultipleClass.__bases__[2].__dict__["non_chimera_method"], MethodWrapper
        )

        assert (
            MultipleClass.__dict__[CONFIG_ATTRIBUTE_NAME]["base_config"] == "overridden"
        )
        assert MultipleClass.__dict__[CONFIG_ATTRIBUTE_NAME]["single_config"] is True
        assert (
            MultipleClass.__dict__[CONFIG_ATTRIBUTE_NAME]["another_base_config"] is True
        )
        assert MultipleClass.__dict__[CONFIG_ATTRIBUTE_NAME]["multiple_config"] is True

    def test_method_wrapper(self):

        class Test(ChimeraObject):
            def do_foo(self, a, b, c=None):
                assert isinstance(self, Test)

                return True

        t = Test()

        assert t.do_foo(1, 2, 3) is True

    def test_config(self):

        class ConfigTest(ChimeraObject):

            __config__ = {"key1": True, "key2": False}

        c = ConfigTest()

        # get
        assert c["key1"] is True
        assert c["key2"] is False

        assert c.__getitem__("key1") is True
        assert c.__getitem__("key2") is False

        # set

        # setitem returns the old item
        assert c.__setitem__("key1", False) is True

        c["key1"] = False
        assert c["key1"] is False

        # oops, only bools
        c["key1"] = True

        with pytest.raises(OptionConversionException):
            c.__setitem__("key1", "Am I a bool?")

        assert c["key1"] is True

        # oops, what?
        with pytest.raises(KeyError):
            c.__getitem__("frog")
        with pytest.raises(TypeError):
            c.__getitem__(100)

    def test_main(self):

        class MainTest(ChimeraObject):

            def __init__(self):
                ChimeraObject.__init__(self)

                self.counter = 0

            def control(self):
                """
                Execute ten times per second (10Hz) and stop after 1 s,
                in other words, when counter = frequency
                """

                self.counter += 1
                return self.counter < self.get_hz()

        m = MainTest()
        m.set_hz(10)

        assert m.__main__() is True
        assert m.counter == m.get_hz()

    def test_location(self):

        class Foo(ChimeraObject):
            pass

        f = Foo()

        assert f.__set_location__("/Foo/bar") is True
        with pytest.raises(InvalidLocationException):
            f.__set_location__("Siberian Lakes")
        assert f.get_location() == "/Foo/bar"

    def test_state(self):

        class Foo(ChimeraObject):
            pass

        f = Foo()

        assert f.get_state() == State.STOPPED, "Initial object state MUST be STOPPED"

        # setstate returns oldstate
        assert f.__set_state__(State.RUNNING) == State.STOPPED
        assert f.get_state() == State.RUNNING

    def test_methods(self):

        class BaseClass(ChimeraObject):

            __config__ = {"base_config": True}

            @event
            def base_event(self):
                pass

            def base_method(self):
                pass

            def _base_private_method(self):
                pass

        class Minimo(BaseClass):

            CONST = 42

            def __init__(self):
                ChimeraObject.__init__(self)
                self.answer = 42

            def __start__(self):
                return True

            def __stop__(self):
                return True

            def do_method(self):
                return self.answer

            # def do_event(self):
            #    self.event_done("Event works!")

            def do_raise(self):
                raise Exception(str(self.answer))

            @staticmethod
            def do_static():
                return 42

            @classmethod
            def do_class(cls):
                return cls.CONST

        m = Minimo()

        # normal bounded methods
        assert m.do_method() == 42

        # unbounded methods (our wrapper is a real duck ;)
        assert Minimo.do_method(m) == 42

        # unbound must pass instance of the class as first parameter
        with pytest.raises(TypeError):
            Minimo.do_method()

        # static methods
        # FIXME: fix test
        # assert m.do_static() == 42
        # assert Minimo.do_static() == 42

        # class methods
        assert m.do_class() == 42
        assert Minimo.do_class() == 42

        # exceptions
        with pytest.raises(Exception):
            m.do_raise()

        # features
        assert m.features(BaseClass)  # Minimo is a BaseClass subclass
        assert not m.features(str)  # But not a basestring subclass
