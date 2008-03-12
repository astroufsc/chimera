#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import sys
import traceback

from chimera.core.exceptions import ClassLoaderException

class ClassLoader (object):
    
    def __init__ (self):
        self._cache = {}

    def loadClass (self, clsname, path = ['.']):
        return self._lookupClass (clsname, path)

    def reloadClass (self, clsname):
        pass

    def _lookupClass (self, clsname, path):

        """
        Based on this recipe
        http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52241
        by Jorgen Hermann
        """

        if clsname in self._cache:
            return self._cache[clsname]

        sys.path = path + sys.path

        try:

            module = __import__(clsname.lower(), globals(), locals(), [clsname])

        except ImportError:

            # Python trick: An ImportError exception catched here
            # could came from both the __import__ above or from the
            # module imported by the __import__ above... So, we need a
            # way to know the difference between those exceptions.  A
            # simple (reliable?) way is to use the length of the
            # exception traceback as a indicator. If the traceback had
            # only 1 entry, the exceptions comes from the __import__
            # above, more than one the exception comes from the
            # imported module

            tb_size = len(traceback.extract_tb(sys.exc_info()[2]))

            # ImportError above
            if tb_size == 1:
                raise ClassLoaderException ("Couldn't found module %s (%s)." % (clsname, path))

            # ImportError on loaded module
            else:
                raise ClassLoaderException ("Module %s found but couldn't be loaded." % clsname)

        except:
            raise ClassLoaderException ("Module %s found but couldn't be loaded." % clsname)

        # turns sys.path back
        [sys.path.remove (p) for p in path]
        
        if not clsname in vars(module).keys():
            raise ClassLoaderException ("Module found but there are no class named %s on module '%s' (%s)." %
                                        (clsname, clsname.lower(), module.__file__))

        self._cache[clsname] = vars(module)[clsname]

        return self._cache[clsname]

