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

from chimera.instruments.telescope import Telescope
from chimera.drivers.faketelescope import FakeTelescope

from chimera.drivers.meade import Meade


from chimera.instruments.camera import Camera
from chimera.drivers.fakecamera import FakeCamera

from chimera.drivers.sbig import SBIG

from chimera.interfaces.cameradriver import Device

import chimera.core.log
#chimera.core.log.setConsoleLevel(logging.DEBUG)

from chimera.util.coord    import Coord
from chimera.util.position import Position

class TestTelescope (object):

    def setup (self):

        self.manager = Manager(port=8000)

        self.manager.addClass(Site, "lna", {"name": "LNA",
                                            "latitude": "-22 32 03",
                                            "longitude": "-45 34 57",
                                            "altitude": "1896",
                                            "utc_offset": "-3"})

        self.manager.addClass(Meade, "meade", {"device": "/dev/ttyS6"})
        self.manager.addClass(Telescope, "meade", {"driver": "/Meade/meade"})

        self.manager.addClass(SBIG, "sbig", {"device": Device.USB})
        self.manager.addClass(Camera, "cam", {"driver": "/SBIG/sbig"})



        #self.manager.addClass(Telescope, "meade",
        #                      {"driver": "200.131.64.134:7666/TheSkyTelescope/0"})


    def test_auto_focus (self):

        cam = self.manager.getProxy(Camera)

        frames = 0

        try:
            frames = cam.expose(exp_time=1, frames=5, interval=0.5, filename="test_expose.fits")
        except Exception, e:
            log.exception("problems")

        assert len(frames) == 5        


        
