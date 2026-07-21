# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import datetime as dt
import time

from chimera.core.site import Site


def test_real_time_by_default():
    site = Site()
    assert site["time_speedup"] == 1.0
    assert site["time_start"] == ""
    assert site.time_speedup() == 1.0

    before = dt.datetime.now(dt.UTC)
    now = site.ut()
    after = dt.datetime.now(dt.UTC)
    assert before <= now <= after


def test_time_start_jumps_the_clock():
    site = Site()
    site["time_start"] = "2026-07-20 23:00:00"

    now = site.ut()
    assert now.year == 2026
    assert now.month == 7
    assert now.day == 20
    assert now.hour == 23
    assert now.tzinfo is not None


def test_naive_time_start_is_read_as_ut():
    site = Site()
    site["time_start"] = "2026-07-20T23:00:00"
    assert site.ut().utcoffset() == dt.timedelta(0)


def test_speedup_scales_elapsed_time():
    site = Site()
    site["time_speedup"] = 600.0
    site["time_start"] = "2026-07-20 23:00:00"
    assert site.time_speedup() == 600.0

    first = site.ut()  # anchors the clock
    time.sleep(0.1)
    elapsed = (site.ut() - first).total_seconds()

    # 0.1 s of wall time is ~60 s of simulated time; the bounds are wide
    # because the sleep only guarantees a lower bound on real elapsed time
    assert 30.0 < elapsed < 300.0


def test_localtime_follows_the_simulated_clock():
    site = Site()
    site["time_start"] = "2026-07-20 23:00:00"

    # localtime must derive from ut(), or a fast-forwarded night still asks
    # the real clock whether it is morning or evening
    assert abs(site.localtime() - site.ut()) < dt.timedelta(seconds=1)
    assert site.localtime().year == 2026


def test_mjd_uses_the_simulated_clock():
    site = Site()
    site["time_start"] = "2026-07-20 23:00:00"

    # 2026-07-20 23:00 UT
    assert abs(site.mjd() - 61241.958333) < 1e-3
