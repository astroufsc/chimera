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
from chimera.core.site     import Site

from chimera.instruments.focuser  import Focuser
from chimera.interfaces.focuser   import InvalidFocusPositionException

from chimera.drivers.fakefocuser  import FakeFocuser
from chimera.drivers.optectcfs    import OptecTCFS

import chimera.core.log
#chimera.core.log.setConsoleLevel(logging.DEBUG)

from nose.tools import assert_raises


class TestFocuser (object):

    def setup (self):

        self.manager = Manager(port=8000)

        self.manager.addClass(Site, "lna", {"name": "LNA",
                                            "latitude": "-22 32 03",
                                            "longitude": "-45 34 57",
                                            "altitude": "1896",
                                            "utc_offset": "-3"})

        #self.manager.addClass(FakeFocuser, "fake", {"device": "/dev/ttyS0"})
        #self.manager.addClass(Focuser, "focus", {"driver": "/FakeFocuser/0"})

        self.manager.addClass(OptecTCFS, "optec", {"device": "/dev/ttyS0"})
        self.manager.addClass(Focuser, "focus", {"driver": "/OptecTCFS/0"})

    def test_get_position (self):

        focus = self.manager.getProxy(Focuser)

        assert focus.getPosition() >= 0

    def test_move (self):

        focus = self.manager.getProxy(Focuser)

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


        

        
