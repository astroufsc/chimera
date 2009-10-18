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

from chimera.core.manager  import Manager
from chimera.core.callback import callback

# hack for event  triggering asserts
FiredEvents = {}


class FilterWheelTest (object):

    FILTER_WHEEL = ""

    def assertEvents(self):

        assert "filterChange" in FiredEvents
        assert isinstance(FiredEvents["filterChange"][1], str)
        assert isinstance(FiredEvents["filterChange"][2], str)
        
    def setupEvents(self):

        @callback(self.manager)
        def filterChangeClbk(newFilter, oldFilter):
            FiredEvents["filterChange"] = (time.time(), newFilter, oldFilter)

        fw = self.manager.getProxy(self.FILTER_WHEEL)
        fw.filterChange += filterChangeClbk
        
    def test_filters (self):

        f = self.manager.getProxy(self.FILTER_WHEEL)
        
        filters = f.getFilters()

        for filter in filters:
            f.setFilter(filter)
            assert f.getFilter() == filter
            self.assertEvents()            

    def test_get_filters (self):
        
        f = self.manager.getProxy(self.FILTER_WHEEL)
        filters = f.getFilters()

        assert isinstance(filters, tuple) or isinstance(filters, list)


#
# setup real and fake tests
#

from chimera.instruments.tests.base import FakeHardwareTest, RealHardwareTest

class TestFakeFilterWheel(FakeHardwareTest, FilterWheelTest):

    def setup (self):

        self.manager = Manager(port=8000)

        from chimera.instruments.fakefilterwheel import FakeFilterWheel
        self.manager.addClass(FakeFilterWheel, "fake", {"device": "/dev/ttyS0",
                                                        "filters": "U B V R I"})
        self.FILTER_WHEEL = "/FakeFilterWheel/0"

        FiredEvents = {}
        self.setupEvents()

    def teardown (self):
        self.manager.shutdown()


class TestRealFilterWheel(RealHardwareTest, FilterWheelTest):
    
    def setup (self):

        self.manager = Manager()

        from chimera.instruments.sbig import SBIG
        self.manager.addClass(SBIG, "sbig", {"filters": "R G B LUNAR CLEAR"})
        self.FILTER_WHEEL = "/SBIG/0"

        FiredEvents = {}
        self.setupEvents()

    def teardown (self):
        self.manager.shutdown()
