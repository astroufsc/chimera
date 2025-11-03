from chimera.core.exceptions import (
    ChimeraException,
    ClassLoaderException,
    ObjectNotFoundException,
)
from chimera.core.path import ChimeraPath


def get_image_server(chimera_object):


    to_return = chimera_object.get_proxy("/ImageServer/0")

    # try:
    #     to_return = chimera_object.get_proxy("/ImageServer/0")
    # except ObjectNotFoundException:
    #     try:
    #         to_return = chimera_object.get_manager().add_location(
    #             "/ImageServer/imageserver", ChimeraPath().controllers
    #         )
    #     except Exception:
    #         raise ClassLoaderException("Unable to create imageserver")

    # if not to_return:
    #     raise ClassLoaderException("Unable to create or find an ImageServer")

    return to_return


class ImageServerException(ChimeraException):
    pass


class InvalidFitsImageException(ImageServerException):
    pass
