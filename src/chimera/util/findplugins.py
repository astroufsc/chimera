import os
from pkgutil import iter_modules


def find_chimera_plugins(prefix="chimera_"):
    """
    Returns chimera plugins paths for instruments and controllers.

    :param prefix: Prefix of the plugins package names.
    """

    instruments_path = []
    controllers_path = []
    for i in iter_modules():
        if i[1].startswith(prefix):
            dirname = os.path.dirname(i[0].find_spec(i[1]).origin)
            if os.path.isdir(f"{dirname}/controllers"):
                controllers_path.append(f"{dirname}/controllers")
            if os.path.isdir(f"{dirname}/instruments"):
                instruments_path.append(f"{dirname}/instruments")

    return controllers_path, instruments_path
