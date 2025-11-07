# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import random

import pytest

from chimera.core.manager import Manager
from chimera.core.site import Site
from chimera.interfaces.focuser import InvalidFocusPositionException

from .base import FakeHardwareTest, RealHardwareTest


class FocuserTest:
    FOCUSER = ""

    def test_get_position(self):
        focus = self.manager.get_proxy(self.FOCUSER)

        assert focus.get_position() >= 0

    def test_move(self):
        focus = self.manager.get_proxy(self.FOCUSER)

        start = focus.get_position()
        delta = int(random.Random().random() * 1000)

        # assumes IN moving to lower values
        focus.move_in(delta)
        assert focus.get_position() == start - delta

        # assumes OUT moving to larger values
        start = focus.get_position()
        focus.move_out(delta)
        assert focus.get_position() == start + delta

        # TO
        focus.move_to(1000)
        assert focus.get_position() == 1000

        # TO where?
        with pytest.raises(InvalidFocusPositionException):
            focus.move_to(1e9)


#
# setup real and fake tests
#
class TestFakeFocuser(FakeHardwareTest, FocuserTest):
    def setup(self):
        self.manager = Manager(port=8000)
        self.manager.add_class(
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

        self.manager.add_class(FakeFocuser, "fake", {"device": "/dev/ttyS0"})
        self.FOCUSER = "/FakeFocuser/0"

    def teardown(self):
        self.manager.shutdown()


class TestRealFocuser(RealHardwareTest, FocuserTest):
    def setup(self):
        self.manager = Manager(port=8000)
        self.manager.add_class(
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

        self.manager.add_class(OptecTCFS, "optec", {"device": "/dev/ttyS4"})
        self.FOCUSER = "/OptecTCFS/0"

    def teardown(self):
        self.manager.shutdown()
