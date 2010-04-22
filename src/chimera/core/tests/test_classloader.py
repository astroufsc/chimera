
from chimera.core.classloader import ClassLoader, ClassLoaderException

from nose.tools import assert_raises

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
        
        assert_raises (ClassLoaderException, loader.loadClass, "ClassLoaderHelperNotFound")       
        assert_raises (ClassLoaderException, loader.loadClass, "ClassLoaderHelperFoundWithoutClass")
        assert_raises (ClassLoaderException, loader.loadClass, "ClassLoaderHelperFoundNotWorking1")
