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

from chimera.controllers.autofocus import Autofocus, Target

from chimera.instruments.camera import Camera
from chimera.drivers.fakecamera import FakeCamera
from chimera.drivers.sbig       import SBIG

from chimera.instruments.focuser import Focuser
from chimera.drivers.fakefocuser import FakeFocuser
from chimera.drivers.optectcfs   import OptecTCFS

import chimera.core.log
chimera.core.log.setConsoleLevel(logging.DEBUG)

class TestAutofocus (object):

    def setup (self):

        self.manager = Manager(port=8000)

        # fake
        #self.manager.addClass(FakeCamera, "fake")
        #self.manager.addClass(Camera, "cam", {"driver": "/FakeCamera/fake"})

        #self.manager.addClass(FakeFocuser, "fake")
        #self.manager.addClass(Focuser, "focus", {"driver": "/FakeFocuser/0"})

        # real
        #self.manager.addClass(SBIG, "sbig", {"device": "USB"})
        #self.manager.addClass(Camera, "cam", {"driver": "/SBIG/0"})

        #self.manager.addClass(OptecTCFS, "optec", {"device": "/dev/ttyS0"})
        #self.manager.addClass(Focuser, "focus", {"driver": "/OptecTCFS/0"})

        self.manager.addClass(Autofocus, "autofocus", {"camera" : "200.131.64.203:7666/Camera/0",
                                                       "focuser": "200.131.64.203:7666/Focuser/0"})

        #self.manager.addClass(Autofocus, "autofocus", {"camera" : "/Camera/0",
        #                                               "focuser": "/Focuser/0"})

        @callback(self.manager)
        def exposeBeginClbk(exp_time):
            print time.time(), "Expose begin for %.3f s." % exp_time

        @callback(self.manager)
        def exposeCompleteClbk():
            print time.time(), "Expose complete."

        @callback(self.manager)
        def readoutBeginClbk(frame):
            print time.time(), "Readout begin for %s." % frame

        @callback(self.manager)
        def readoutCompleteClbk(frame):
            print time.time(), "Readout complete for %s." % frame

        @callback(self.manager)
        def abortCompleteClbk():
            print time.time(), "Abort complete."

        cam = self.manager.getProxy(Camera, host='200.131.64.203', port=7666)
        cam.exposeBegin     += exposeBeginClbk
        cam.exposeComplete  += exposeCompleteClbk        
        cam.readoutBegin    += readoutBeginClbk        
        cam.readoutComplete += readoutCompleteClbk
        cam.abortComplete   += abortCompleteClbk

    def teardown (self):
        self.manager.shutdown()
        del self.manager

    def test_focus (self):

        autofocus = self.manager.getProxy(Autofocus)

        #autofocus += {"save_frames": True}

        best_focus = autofocus.focus(target=Target.CURRENT, exptime=10, start=0, end=7000, step=1000, minmax=(0,30))
        #best_focus = autofocus.focus(target=Target.CURRENT, exptime=10, points=25, minmax=(0,30))

        best_focus.plot("focus-lna.png")
        best_focus.log("focus-lna.txt")


