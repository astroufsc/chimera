

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.methodwrapper import MethodWrapper
from chimera.core.event         import event
from chimera.core.state         import State
from chimera.core.config        import OptionConversionException
from chimera.core.exceptions    import InvalidLocationException
from chimera.core.constants     import CONFIG_ATTRIBUTE_NAME

from nose.tools import assert_raises

class TestChimeraObject (object):

    # FIXME: use fixtures to put each test on their own method (unit tests in small units!)
    def test_class_creation (self):

        # 1. simple class (no inheritance)
        class BaseClass (ChimeraObject):

            __config__ = {"baseConfig": True}
            
            @event
            def baseEvent (self):
                pass
            def baseMethod (self):
                pass
            def _basePrivateMethod (self):
                pass

        # NOTE: we don't use getattr to avoid descriptor protocol,
        #       which will bind the method when we call getattr

        assert isinstance(BaseClass.__dict__['baseMethod'], MethodWrapper)
        assert isinstance(BaseClass.__dict__['baseEvent'], MethodWrapper)

        assert not isinstance(BaseClass.__dict__['_basePrivateMethod'], MethodWrapper)

        assert BaseClass.__dict__[CONFIG_ATTRIBUTE_NAME]['baseConfig'] == True

        # 2. single inheritance
        class SingleClass (BaseClass):

            __config__ = {"singleConfig": True}
            
            @event
            def singleEvent (self):
                pass
            def singleMethod (self):
                pass

        assert isinstance(SingleClass.__bases__[0].__dict__['baseMethod'], MethodWrapper)
        assert isinstance(SingleClass.__dict__['singleMethod'], MethodWrapper)
        assert isinstance(SingleClass.__dict__['singleEvent'], MethodWrapper)        

        assert not isinstance(SingleClass.__bases__[0].__dict__['_basePrivateMethod'], MethodWrapper)

        assert SingleClass.__dict__[CONFIG_ATTRIBUTE_NAME]['baseConfig'] == True
        assert SingleClass.__dict__[CONFIG_ATTRIBUTE_NAME]['singleConfig'] == True

        # 3. multiple inheritance
        class AnotherBase (ChimeraObject):
            __config__ = {"anotherBaseConfig": True}
            def anotherBaseMethod (self):
                pass

        class NonChimeraClass (object):
            __config__ = {}
            def nonChimeraMethod (self):
                pass

        class MultipleClass (SingleClass, AnotherBase, NonChimeraClass):
            __config__ = {"multipleConfig": True,
                          "baseConfig": "overriden"}

            def multipleMethod (self):
                pass

        assert isinstance(MultipleClass.__dict__['multipleMethod'], MethodWrapper)
        assert isinstance(MultipleClass.__bases__[0].__dict__['singleMethod'], MethodWrapper)
        assert isinstance(MultipleClass.__bases__[1].__dict__['anotherBaseMethod'], MethodWrapper)

        assert not isinstance(MultipleClass.__bases__[2].__dict__['nonChimeraMethod'], MethodWrapper)        

        assert MultipleClass.__dict__[CONFIG_ATTRIBUTE_NAME]['baseConfig'] == "overriden"
        assert MultipleClass.__dict__[CONFIG_ATTRIBUTE_NAME]['singleConfig'] == True
        assert MultipleClass.__dict__[CONFIG_ATTRIBUTE_NAME]['anotherBaseConfig'] == True
        assert MultipleClass.__dict__[CONFIG_ATTRIBUTE_NAME]['multipleConfig'] == True

    def test_method_wrapper (self):

        class Test (ChimeraObject):
            def doFoo (self, a, b, c = None):
                assert type(self) == Test

                return True

        t = Test()

        assert t.doFoo(1, 2, 3) == True


    def test_config (self):

        class ConfigTest (ChimeraObject):

            __config__ = {"key1": True,
                          "key2": False}


        c = ConfigTest()

        # get
        assert c["key1"] == True
        assert c["key2"] == False

        assert c.__getitem__("key1") == True
        assert c.__getitem__("key2") == False

        # set

        # setitem returns the old item
        assert c.__setitem__ ("key1", False) == True

        c["key1"] = False        
        assert c["key1"] == False

        # oops, only bools
        c["key1"] = True
        
        assert_raises(OptionConversionException, c.__setitem__, "key1", "Am I a bool?")

        assert c["key1"] == True

        # oops, what?
        assert_raises (KeyError, c.__getitem__, "frog")
        assert_raises (TypeError, c.__getitem__, 100)        

    def test_main (self):

        class MainTest (ChimeraObject):

            def __init__ (self):
                ChimeraObject.__init__(self)

                self.counter = 0

            def control (self):
                """
                Execute ten times per second (10Hz) and stop after 1 s,
                in other words, when counter = frequency
                """
                
                self.counter += 1
                return self.counter < self.getHz()

        m = MainTest()
        m.setHz(10)

        assert m.__main__() == True
        assert m.counter == m.getHz()

    def test_location (self):

        class Foo (ChimeraObject): pass

        f = Foo()

        assert f.__setlocation__ ('/Foo/bar') == True
        assert_raises(InvalidLocationException, f.__setlocation__, 'Siberian Lakes')
        assert f.getLocation () == '/Foo/bar'

    def test_state (self):
        
        class Foo (ChimeraObject): pass

        f = Foo()

        assert f.getState() == State.STOPPED, "Initial object state MUST be STOPPED"

        # setstate returns oldstate
        assert f.__setstate__ (State.RUNNING) == State.STOPPED
        assert f.getState() == State.RUNNING

    

    def test_methods (self):

        class Minimo (ChimeraObject):

            CONST = 42

            def __init__(self):
                ChimeraObject.__init__ (self)
                self.answer = 42

            def __start__ (self):
                return True

            def __stop__ (self):
                return True

            def doMethod (self):
                return self.answer

            #def doEvent (self):
            #    self.eventDone("Event works!")

            def doRaise (self):
                raise Exception(str(self.answer))

            @staticmethod
            def doStatic ():
                return 42

            @classmethod
            def doClass (cls):
                return cls.CONST

        m = Minimo()

        # normal bounded methods
        assert m.doMethod() == 42

        # unbounded methods (our wrapper is a real duck ;)
        assert Minimo.doMethod(m) == 42

        # unbound must pass instance of the class as first parameter
        assert_raises(TypeError, Minimo.doMethod, ())

        # static methods
        assert m.doStatic() == 42
        assert Minimo.doStatic() == 42

        # class methods
        assert m.doClass() == 42
        assert Minimo.doClass() == 42

        # exceptions
        assert_raises(Exception, m.doRaise, ())

