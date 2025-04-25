from chimera.core.exceptions import (
    ChimeraException,
    ObjectNotFoundException,
    ClassLoaderException,
)
from chimera.core.path import ChimeraPath


def get_image_server(manager):

    try:
        to_return = manager.get_proxy("/ImageServer/0")
    except ObjectNotFoundException:
        try:
            to_return = manager.add_location(
                "/ImageServer/imageserver", ChimeraPath().controllers
            )
        except Exception:
            raise ClassLoaderException("Unable to create imageserver")

    if not to_return:
        raise ClassLoaderException("Unable to create or find an ImageServer")

    return to_return


class ImageServerException(ChimeraException):
    pass


class InvalidFitsImageException(ImageServerException):
    pass
