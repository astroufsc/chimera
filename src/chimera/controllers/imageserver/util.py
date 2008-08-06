from chimera.core.manager import Manager
from chimera.core.exceptions import ObjectNotFoundException, ClassLoaderException
from chimera.core.path import ChimeraPath
import Pyro.util

def getImageServer():
    manager = Manager.getManagerProxy()
    try:
        toReturn = manager.getProxy('/ImageServer/0')
    except ObjectNotFoundException:
        try:
            toReturn = manager.addLocation('/ImageServer/imageserver', [ChimeraPath.controllers()])
        except Exception, e:
            print ''.join(Pyro.util.getPyroTraceback(e))
            raise ClassLoaderException('Unable to create imageserver')
    except Exception, e:
        print ''.join(Pyro.util.getPyroTraceback(e))
        raise ClassLoaderException('Unable to create imageserver')
    if not toReturn:
        raise ClassLoaderException('Unable to create or find an ImageServer')
    return toReturn
