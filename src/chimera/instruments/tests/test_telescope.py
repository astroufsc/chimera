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


from chimera.core.chimeraobject import ChimeraObject
from chimera.core.event         import event

import time


class Telescope (ChimeraObject):

    __config__ = {"slew_rate": "max"}
    
    def __init__ (self):
        ChimeraObject.__init__ (self)

    def __start__ (self):
        print "[%s] starting at %s"% (self.getLocation(), self.getDaemon().hostname)

        self.slewComplete += self.getProxy().slew_cb

        return True
               
    def __stop__ (self):
        print "[%s] stopping at %s"% (self.getLocation(), self.getDaemon().hostname)
        return True

    def slew_cb (self, when):
        print "[callback] slew finished at %s." % time.ctime(when)

    def slew (self, ra, dec):

        print "[invocation] slewing..."

        print "location:", self.getLocation()
        print "state   :", self.getState()
        print "manager :", self.getManager()
        print "proxy   :", self.getProxy()

        self.slewComplete (time.time())

        return True

    def shutdown (self):
        self.getManager().shutdown()        
    
    @event
    def slewComplete (self, when):
        pass

