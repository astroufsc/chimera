import pytest

from chimera.core.classloader import ClassLoader, ClassLoaderException

import time
import os.path

class TestClassLoader:

    def test_load_class (self):

        loader = ClassLoader ()

        t0 = time.time ()
        cls = loader.loadClass ("ClassLoaderHelperWorking", path=[os.path.dirname(__file__)])
        t = time.time ()
        
        assert cls.__name__ == "ClassLoaderHelperWorking"

        # test cache (use time to prove that cache is faster)
        t0 = time.time()
        cls = loader.loadClass ("ClassLoaderHelperWorking", path=[os.path.dirname(__file__)])
        t1 = time.time () - t0
        
        assert cls.__name__ == "ClassLoaderHelperWorking"
        assert t1 < t
        
        # test case in-sensitivite when looking for ClasName
        loader._cache = {} # clear cache
        cls = loader.loadClass ("ClAsSloAdErHeLpErWoRkiNg", path=[os.path.dirname(__file__)])
        
        with pytest.raises(ClassLoaderException):
            loader.loadClass("ClassLoaderHelperNotFound")
        with pytest.raises(ClassLoaderException):
            loader.loadClass("ClassLoaderHelperFoundWithoutClass")
        with pytest.raises(ClassLoaderException):
            loader.loadClass("ClassLoaderHelperFoundNotWorking1")
