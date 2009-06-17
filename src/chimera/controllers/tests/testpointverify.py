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
import sys
import logging

from chimera.core.manager  import Manager
from chimera.core.callback import callback
from chimera.core.site     import Site

from chimera.controllers.pointverify import PointVerify

from chimera.instruments.camera import CameraBase
from chimera.instruments.fakecamera import FakeCamera
from chimera.instruments.sbig       import SBIG

from chimera.instruments.focuser import FocuserBase
from chimera.instruments.fakefocuser import FakeFocuser
from chimera.instruments.optectcfs   import OptecTCFS

from chimera.instruments.telescope import TelescopeBase
from chimera.instruments.faketelescope import FakeTelescope
from chimera.instruments.meade   import Meade



import chimera.core.log
chimera.core.log.setConsoleLevel(logging.DEBUG)

class TestPointVerify (object):

    def setup (self):

        self.manager = Manager(port=8000)

        # real

        self.manager.addClass(Site, "lna", {"name": "UFSC",
                                            "latitude": "-27 36 13 ",
                                            "longitude": "-48 31 20",
                                            "altitude": "20",
                                            "utc_offset": "-3"})

        #self.manager.addClass(Meade, "meade", {"device": "/dev/ttyS6"})
        self.manager.addClass(TelescopeBase, "meade")
        self.manager.addClass(FakeTelescope, "faket")
        self.manager.addClass(CameraBase, "sbig")
        self.manager.addClass(FakeCamera,"fakec")

        self.manager.addClass(PointVerify, "Point")



    def teardown (self):
        self.manager.shutdown()
        del self.manager

    def test_point (self):

        print "LALa"
        point = self.manager.getProxy(PointVerify)
        point.pointVerify()
        print "LALA"
