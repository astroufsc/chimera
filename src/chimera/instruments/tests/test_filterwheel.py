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


import time
import logging
import random

from chimera.core.manager  import Manager
from chimera.core.callback import callback

from chimera.instruments.filterwheel import FilterWheel

from chimera.drivers.fakefilterwheel import FakeFilterWheel

from chimera.drivers.sbig import SBIG
from chimera.interfaces.cameradriver import Device


import chimera.core.log
#chimera.core.log.setConsoleLevel(logging.DEBUG)

from nose.tools import assert_raises


class TestFilterWheel (object):

    def setup (self):

        self.manager = Manager(port=8000)

        #self.manager.addClass(FakeFilterWheel, "fake", {"device": "/dev/ttyS0"})
        #self.manager.addClass(FilterWheel, "filter", {"driver": "/FakeFilterWheel/0",
        #                                              "filters": "U B V R I"})

        self.manager.addClass(SBIG, "sbig", {"device": Device.USB})
        self.manager.addClass(FilterWheel, "filter", {"driver": "/SBIG/0",
                                                      "filters": "U B V R I"})


        @callback(self.manager)
        def filterChangeClbk (new, old):
            #print "[filter change] new: %s,  old: %s" % (new, old)
            pass

        f = self.manager.getProxy(FilterWheel)
        f.filterChange += filterChangeClbk

    def test_get_filter (self):

        f = self.manager.getProxy(FilterWheel)
        f.getFilter()

    def test_set_filter (self):

        f = self.manager.getProxy(FilterWheel)
        
        filters = f.getFilters()

        for filter in filters:
            f.setFilter(filter)

    def test_get_filters (self):
        
        f = self.manager.getProxy(FilterWheel)
        filters = f.getFilters()

        assert isinstance(filters, tuple) or isinstance(filters, list)

        
        

