#! /usr/bin/python
# -*- coding: iso8859-1 -*-

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

from chimera.core.lifecycle import BasicLifeCycle
from chimera.core.event import event
from chimera.core.config import OptionConversionException

from chimera.interfaces.filterwheel import IFilterWheel

import logging

class FilterWheel (BasicLifeCycle, IFilterWheel):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init(self, config):

        self.config += config

        self.drv = self.manager.getDriver(self.config.driver)

        if not self.drv:
            logging.debug("Couldn't load selected driver (%ss)." %  self.config.driver)
            return False

        # connect events
        self.drv.filterChanged += self.filter_cb

        return True

    # callbacks
    def filter_cb (self, new, old):
        self.filterChanged (new, old)

    def getFilter (self):
        return self.drv.getFilter ()

    def setFilter (self, _filter):

        try:
            self.config.filters = _filter
        except OptionConversionException:
            logging.error ("Filter '%s' not defined." %  _filter)
            return False
        
        return self.drv.setFilter (eval ("self.config.%s" % _filter))
        
    def getFilterStatus (self):
        return self.drv.getFilterStatus ()
