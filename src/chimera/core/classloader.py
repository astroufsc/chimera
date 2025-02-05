# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import sys
import traceback

from chimera.core.exceptions import ClassLoaderException


class ClassLoader(object):

    def __init__(self):
        self._cache = {}

    def loadClass(self, clsname, path=["."]):
        return self._lookupClass(clsname, path)

    def _lookupClass(self, clsname, path):
        """
        Based on this recipe
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52241
        by Jorgen Hermann
        """

        if clsname.lower() in self._cache:
            return self._cache[clsname.lower()]

        if not isinstance(path, (list, tuple)):
            path = [path]

        sys.path = path + sys.path

        try:

            module = __import__(clsname.lower(), globals(), locals(), [clsname])

        except ImportError:

            # Python trick: An ImportError exception caught here
            # could come from both the __import__ above or from the
            # module imported by the __import__ above... So, we need a
            # way to know the difference between those exceptions.  A
            # simple (reliable?) way is to use the length of the
            # exception traceback as an indicator. If the traceback had
            # only 1 entry, the exceptions comes from the __import__
            # above, more than one the exception comes from the
            # imported module

            tb_size = len(traceback.extract_tb(sys.exc_info()[2]))

            # ImportError above
            if tb_size == 1:
                raise ClassLoaderException(f"Couldn't find module {clsname} ({path}).")

            # ImportError on loaded module
            else:
                raise ClassLoaderException(
                    f"Module {clsname} found but couldn't be loaded."
                )

        except Exception:
            # Catch any other exception during import
            raise ClassLoaderException(
                f"Module {clsname} found but couldn't be loaded."
            )

        # turns sys.path back
        [sys.path.remove(p) for p in path]

        cls = None

        for k, v in list(vars(module).items()):
            if k.lower() == clsname.lower():
                cls = v
                break

        if not cls:
            raise ClassLoaderException(
                f"Module found but couldn't fount class on module '{clsname.lower()}' ({module.__file__})."
            )

        self._cache[clsname.lower()] = cls

        return self._cache[clsname.lower()]
