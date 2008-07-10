
import os

have_pkg_resources = True

try:
    import pkg_resources
except ImportError:
    have_pkg_resources = False

__all__ = ['ChimeraPath']


class ChimeraPath (object):

    @staticmethod
    def root ():
        if have_pkg_resources:
            try:
                pkgs = pkg_resources.require('chimera-python')
                chimera = pkgs[0]
                return os.path.realpath(os.path.join(chimera.location, 'chimera'))
            except pkg_resources.DistributionNotFound:
                pass

        return os.path.realpath(os.path.join(os.path.abspath(__file__), '../../'))

    @staticmethod
    def instruments ():
        return os.path.join(ChimeraPath.root(), 'instruments')

    @staticmethod
    def controllers ():
        return os.path.join(ChimeraPath.root(), 'controllers')

    @staticmethod                                
    def drivers ():
        return os.path.join(ChimeraPath.root(), 'drivers')

