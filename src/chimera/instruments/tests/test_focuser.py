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

import random

from chimera.core.manager  import Manager
from chimera.core.site     import Site

from chimera.interfaces.focuser   import InvalidFocusPositionException

from nose.tools import assert_raises


class FocuserTest (object):

    FOCUSER = ""

    def test_get_position (self):

        focus = self.manager.getProxy(self.FOCUSER)

        assert focus.getPosition() >= 0

    def test_move (self):

        focus = self.manager.getProxy(self.FOCUSER)

        start = focus.getPosition()
        delta = int(random.Random().random()*1000)

        # assumes IN moving to lower values        
        focus.moveIn(delta)
        assert focus.getPosition() == start-delta

        # assumes OUT moving to larger values
        start = focus.getPosition()
        focus.moveOut(delta)
        assert focus.getPosition() == start+delta

        # TO
        focus.moveTo(1000)
        assert focus.getPosition() == 1000

        # TO where?
        assert_raises(InvalidFocusPositionException, focus.moveTo, 1e9)


#
# setup real and fake tests
#

from chimera.instruments.tests.base import FakeHardwareTest, RealHardwareTest

class TestFakeFocuser(FakeHardwareTest, FocuserTest):

    def setup(self):

        self.manager = Manager(port=8000)
        self.manager.addClass(Site, "lna", {"name": "LNA",
                                            "latitude": "-22 32 03",
                                            "longitude": "-45 34 57",
                                            "altitude": "1896",
                                            "utc_offset": "-3"})

        from chimera.instruments.fakefocuser import FakeFocuser
        self.manager.addClass(FakeFocuser, "fake", {"device": "/dev/ttyS0"})
        self.FOCUSER = "/FakeFocuser/0"

    def teardown (self):
        self.manager.shutdown()

    
class TestRealFocuser(RealHardwareTest, FocuserTest):
    
    def setup (self):
        self.manager = Manager(port=8000)
        self.manager.addClass(Site, "lna", {"name": "LNA",
                                            "latitude": "-22 32 03",
                                            "longitude": "-45 34 57",
                                            "altitude": "1896",
                                            "utc_offset": "-3"})
        from chimera.instruments.optectcfs import OptecTCFS
        self.manager.addClass(OptecTCFS, "optec", {"device": "/dev/ttyS4"})
        self.FOCUSER = "/OptecTCFS/0"

    def teardown (self):
        self.manager.shutdown()

