
from chimera.core.classloader import ClassLoader, ClassLoaderException

from nose.tools import assert_raises

import time

class TestClassLoader:

    def test_load_class (self):

        loader = ClassLoader ()

        t0 = time.time ()
        cls = loader.loadClass ("ClassLoaderHelperWorking", ["."])
        t = time.time ()
        
        assert cls.__name__ == "ClassLoaderHelperWorking"

        # test cache (use time to prove that cache is faster)
        t0 = time.time()
        cls = loader.loadClass ("ClassLoaderHelperWorking", ["."])
        t1 = time.time () - t0
        
        assert cls.__name__ == "ClassLoaderHelperWorking"
        assert t1 < t
        
        assert_raises (ClassLoaderException, loader.loadClass, "ClassLoaderHelperNotFound")       
        assert_raises (ClassLoaderException, loader.loadClass, "ClassLoaderHelperFoundWithoutClass")
        assert_raises (ClassLoaderException, loader.loadClass, "ClassLoaderHelperFoundNotWorking1")
        assert_raises (ClassLoaderException, loader.loadClass, "ClassLoaderHelperFoundNotWorking2")
