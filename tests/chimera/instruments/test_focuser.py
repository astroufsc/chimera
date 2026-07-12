# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import random

import pytest

from chimera.instruments.fakefocuser import FakeFocuser


@pytest.fixture
def focuser(manager):
    manager.add_class(FakeFocuser, "fake", {"device": "/dev/ttyS0"})
    return manager.get_proxy("/FakeFocuser/0")


class TestFakeFocuser:
    def test_get_position(self, focuser):
        assert focuser.get_position() >= 0

    def test_move(self, focuser):
        start = focuser.get_position()
        delta = int(random.Random().random() * 1000)

        # assumes IN moving to lower values
        focuser.move_in(delta)
        assert focuser.get_position() == start - delta

        # assumes OUT moving to larger values
        start = focuser.get_position()
        focuser.move_out(delta)
        assert focuser.get_position() == start + delta

        # TO
        focuser.move_to(1000)
        assert focuser.get_position() == 1000

        # TO where?
        with pytest.raises(Exception, match="InvalidFocusPositionException"):
            focuser.move_to(1e9)
