
from types import FunctionType

def setAttribute(dict_, name, value):
    for func_name, func in dict_.items():
        if type(func) == FunctionType and not func_name.startswith("_"):
            setattr(func, name, value)

class RealHardwareTestMetaClass(type):
    
    def __new__ (meta, clsname, bases, _dict):
        for base in bases:
            setAttribute(base.__dict__, "real", 1)
        setAttribute(_dict, "real", 1)
        return super(RealHardwareTestMetaClass, meta).__new__(meta, clsname, bases, _dict)
    
class FakeHardwareTestMetaClass(type):
    
    def __new__ (meta, clsname, bases, _dict):
        for base in bases:
            setAttribute(base.__dict__, "fake", 1)
        setAttribute(_dict, "fake", 1)
        return super(FakeHardwareTestMetaClass, meta).__new__(meta, clsname, bases, _dict)

class RealHardwareTest(object):
    __metaclass__ = RealHardwareTestMetaClass
    
class FakeHardwareTest(object):
    __metaclass__ = FakeHardwareTestMetaClass
