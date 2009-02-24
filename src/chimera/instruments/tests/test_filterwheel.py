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

from chimera.core.manager  import Manager


class TestFilterWheel (object):

    FILTER_WHEEL = ""

    def setup (self):

        self.manager = Manager(port=8000)

        if "REAL" in sys.argv:
            from chimera.instruments.sbig import SBIG
            self.manager.addClass(SBIG, "sbig", {"filters": "R G B LUNAR CLEAR"})
            self.FILTER_WHEEL = "/SBIG/0"
        else:
            from chimera.instruments.fakefilterwheel import FakeFilterWheel
            self.manager.addClass(FakeFilterWheel, "fake", {"device": "/dev/ttyS0",
                                                            "filters": "U B V R I"})
            self.FILTER_WHEEL = "/FakeFilterWheel/0"

    def teardown (self):
        self.manager.shutdown()

    def test_filters (self):

        f = self.manager.getProxy(self.FILTER_WHEEL)
        
        filters = f.getFilters()

        for filter in filters:
            f.setFilter(filter)
            assert f.getFilter() == filter

    def test_get_filters (self):
        
        f = self.manager.getProxy(self.FILTER_WHEEL)
        filters = f.getFilters()

        assert isinstance(filters, tuple) or isinstance(filters, list)

        
        

