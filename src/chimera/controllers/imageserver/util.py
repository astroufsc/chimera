from chimera.controllers.imageserver.imageserver import ImageServer
from chimera.util.output import red
from chimera.core.exceptions import (
    ChimeraException,
    ClassLoaderException,
    ObjectNotFoundException,
)
from chimera.core.path import ChimeraPath


def get_image_server(chimera_object) -> ImageServer:


    try:
        to_return = chimera_object.get_proxy("/ImageServer/0")
        to_return.resolve()
        to_return.ping()
    except Exception as e:
        print(red(f"ImageServer not found: {e}"))
        return None

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
