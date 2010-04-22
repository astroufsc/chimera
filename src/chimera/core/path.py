
import os

__all__ = ['ChimeraPath']

class ChimeraPath (object):

    @staticmethod
    def root ():
        return os.path.realpath(os.path.join(os.path.abspath(__file__), '../../'))

    @staticmethod
    def instruments ():
        return os.path.join(ChimeraPath.root(), 'instruments')

    @staticmethod
    def controllers ():
        return os.path.join(ChimeraPath.root(), 'controllers')
