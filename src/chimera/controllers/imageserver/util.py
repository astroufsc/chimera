from chimera.controllers.imageserver.imageserver import ImageServer
from chimera.core.exceptions import (
    ChimeraException,
)


def get_image_server(chimera_object) -> ImageServer:
    try:
        imgsrv = chimera_object.get_proxy("/ImageServer/0")
        imgsrv.ping()
    except Exception:
        return None

    return imgsrv


class ImageServerException(ChimeraException):
    pass


class InvalidFitsImageException(ImageServerException):
    pass
