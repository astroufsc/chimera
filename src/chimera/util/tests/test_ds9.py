
from chimera.util.ds9 import DS9

import os
import signal
import subprocess
import time

class TestDS9(object):

    def test_basics (self):

        ds9 = DS9()
        assert ds9 != None

        ds9.open()
        assert ds9.isOpen() == True
        
        ds9.quit()
        assert ds9.isOpen() == False

    def test_use_global_ds9 (self):

        filename = os.path.realpath(os.path.join(os.path.dirname(__file__), "teste-sem-wcs.fits"))

        p = subprocess.Popen("ds9 %s" % filename, shell=True)
        time.sleep(2)

        ds9 = DS9()
        assert ds9.isOpen() == True
        assert ds9.get("file").strip() == filename

        os.kill(p.pid, signal.SIGTERM)
        ds9.quit()
