# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.instruments.faketelescope import FakeTelescope


def test_equinox_is_numeric():
    # FITS requires EQUINOX to be a float, not the string "NOW" (#228)
    t = FakeTelescope()
    t._ra, t._dec, t._alt, t._az = 10.0, -30.0, 45.0, 120.0
    md = {key: value for key, value, _ in t.get_metadata(None)}
    assert isinstance(md["EQUINOX"], float)
    assert md["EQUINOX"] == 2000.0
