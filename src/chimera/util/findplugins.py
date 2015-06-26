import os
from pkgutil import iter_modules


def find_chimera_plugins(prefix='chimera_'):
    """
    Returns chimera plugins paths for instruments and controllers.

    :param prefix: Prefix of the plugins package names.
    """

    instruments_path = []
    controllers_path = []
    for i in iter_modules():
        if i[1].startswith(prefix):
            fname = i[0].find_module(i[1]).filename
            if os.path.isdir('%s/controllers' % fname):
                controllers_path.append('%s/controllers' % fname)
            if os.path.isdir('%s/instruments' % fname):
                instruments_path.append('%s/instruments' % fname)

    return controllers_path, instruments_path
