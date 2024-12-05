import os
from chimera.util.findplugins import find_chimera_plugins

__all__ = ["ChimeraPath"]


class ChimeraPath(object):

    def __init__(self):
        # Search for chimera plugins on the sys.path
        self._controllers_plugins, self._instruments_plugins = find_chimera_plugins()
        self._instruments = [os.path.join(self.root(), "instruments")]
        self._instruments.extend(self._instruments_plugins)
        self._controllers = [os.path.join(self.root(), "controllers")]
        self._controllers.extend(self._controllers_plugins)

    @staticmethod
    def root():
        return os.path.realpath(os.path.join(os.path.abspath(__file__), "../../"))

    @property
    def instruments(self):
        return self._instruments

    @property
    def controllers(self):
        return self._controllers
