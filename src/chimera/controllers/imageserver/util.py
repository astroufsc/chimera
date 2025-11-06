from chimera.controllers.imageserver.imageserver import ImageServer
from chimera.util.output import red
from chimera.core.exceptions import (
    ChimeraException,
    ClassLoaderException,
)

def get_image_server(chimera_object) -> ImageServer:

    try:
        imgsrv = chimera_object.get_proxy("/ImageServer/0")
        imgsrv.ping()
    except Exception as e:
        raise ClassLoaderException(f"ImageServer not found: {e}")

    return imgsrv


class ImageServerException(ChimeraException):
    pass


class InvalidFitsImageException(ImageServerException):
    pass
