
import Pyro.util

from chimera.core.main import chimera

tel = chimera.Telescope()

try:
    tel.slew("ra", "dec")
    tel.shutdown()
except Exception, e:
    print ''.join(Pyro.util.getPyroTraceback(e))



