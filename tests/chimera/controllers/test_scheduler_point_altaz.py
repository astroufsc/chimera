# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""A point action given alt/az must reach the telescope as plain degrees.

Position.alt/az return floats (Coord.deg) while .ra/.dec return Coords, so
the handler calling .to_d() on all four raised
"'float' object has no attribute 'to_d'" for every alt/az point.
"""

from types import SimpleNamespace

import pytest

from chimera.controllers.scheduler.handlers import PointHandler
from chimera.util.position import Position


class FakeTelescope:
    def __init__(self):
        self.alt_az = None

    def slew_to_alt_az(self, alt, az):
        self.alt_az = (alt, az)


def _action(position):
    return SimpleNamespace(
        target_ra_dec=None,
        target_alt_az=position,
        target_name=None,
        offset_ns=None,
        offset_ew=None,
        dome_tracking=None,
        dome_az=None,
        pa=None,
    )


def test_position_alt_az_are_floats():
    # the premise of the bug: these are NOT Coords
    position = Position.from_alt_az(88.0, 89.0)
    assert isinstance(position.alt, float)
    assert isinstance(position.az, float)


@pytest.fixture
def telescope(monkeypatch):
    fake = FakeTelescope()
    monkeypatch.setattr(PointHandler, "telescope", fake, raising=False)
    monkeypatch.setattr(PointHandler, "dome", None, raising=False)
    monkeypatch.setattr(PointHandler, "rotator", None, raising=False)
    return fake


def test_point_alt_az_slews(telescope):
    PointHandler.process(_action(Position.from_alt_az(88.0, 89.0)))
    assert telescope.alt_az == (88.0, 89.0)
