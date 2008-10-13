
from chimera.core.exceptions import ChimeraException, ObjectNotFoundException, ClassLoaderException
from chimera.core.path import ChimeraPath
import Pyro.util

def getImageServer(manager):

    try:
        toReturn = manager.getProxy('/ImageServer/0')
    except ObjectNotFoundException:
        try:
            toReturn = manager.addLocation('/ImageServer/imageserver', [ChimeraPath.controllers()])
        except Exception, e:
            print ''.join(Pyro.util.getPyroTraceback(e))
            raise ClassLoaderException('Unable to create imageserver')

    if not toReturn:
        raise ClassLoaderException('Unable to create or find an ImageServer')

    return toReturn

class ImageServerException(ChimeraException):
    pass

class InvalidFitsImageException(ImageServerException):
    pass
