# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import random

from chimera.core.manager import Manager
from chimera.core.site import Site

from chimera.interfaces.focuser import InvalidFocusPositionException
from .base import FakeHardwareTest, RealHardwareTest
import pytest


class FocuserTest(object):

    FOCUSER = ""

    def test_get_position(self):

        focus = self.manager.getProxy(self.FOCUSER)

        assert focus.getPosition() >= 0

    def test_move(self):

        focus = self.manager.getProxy(self.FOCUSER)

        start = focus.getPosition()
        delta = int(random.Random().random() * 1000)

        # assumes IN moving to lower values
        focus.moveIn(delta)
        assert focus.getPosition() == start - delta

        # assumes OUT moving to larger values
        start = focus.getPosition()
        focus.moveOut(delta)
        assert focus.getPosition() == start + delta

        # TO
        focus.moveTo(1000)
        assert focus.getPosition() == 1000

        # TO where?
        with pytest.raises(InvalidFocusPositionException):
            focus.moveTo(1e9)


#
# setup real and fake tests
#
class TestFakeFocuser(FakeHardwareTest, FocuserTest):

    def setup(self):

        self.manager = Manager(port=8000)
        self.manager.addClass(
            Site,
            "lna",
            {
                "name": "LNA",
                "latitude": "-22 32 03",
                "longitude": "-45 34 57",
                "altitude": "1896",
            },
        )

        from chimera.instruments.fakefocuser import FakeFocuser

        self.manager.addClass(FakeFocuser, "fake", {"device": "/dev/ttyS0"})
        self.FOCUSER = "/FakeFocuser/0"

    def teardown(self):
        self.manager.shutdown()


class TestRealFocuser(RealHardwareTest, FocuserTest):

    def setup(self):
        self.manager = Manager(port=8000)
        self.manager.addClass(
            Site,
            "lna",
            {
                "name": "LNA",
                "latitude": "-22 32 03",
                "longitude": "-45 34 57",
                "altitude": "1896",
            },
        )

        from chimera.instruments.optectcfs import OptecTCFS

        self.manager.addClass(OptecTCFS, "optec", {"device": "/dev/ttyS4"})
        self.FOCUSER = "/OptecTCFS/0"

    def teardown(self):
        self.manager.shutdown()
