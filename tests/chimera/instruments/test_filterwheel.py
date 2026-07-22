# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import logging
import time

import pytest

from chimera.core.exceptions import ChimeraException, ObjectNotFoundException
from chimera.instruments.fakefilterwheel import FakeFilterWheel
from chimera.interfaces.filterwheel import (
    FocusOffsetException,
    InvalidFilterPositionException,
)

# hack for event triggering asserts
fired_events = {}


def filter_change_clbk(new_filter, old_filter):
    fired_events["filter_change"] = (time.time(), new_filter, old_filter)


@pytest.fixture
def filterwheel(manager):
    manager.add_class(
        FakeFilterWheel, "fake", {"device": "/dev/ttyS0", "filters": "U B V R I"}
    )
    fired_events.clear()

    wheel = manager.get_proxy("/FakeFilterWheel/0")
    wheel.filter_change += filter_change_clbk
    return wheel


class TestFakeFilterWheel:
    def assert_events(self):
        assert "filter_change" in fired_events
        assert isinstance(fired_events["filter_change"][1], str)
        assert isinstance(fired_events["filter_change"][2], str)

    def test_filters(self, filterwheel, wait_for):
        filters = filterwheel.get_filters()

        for filter in filters:
            fired_events.clear()
            filterwheel.set_filter(filter)
            assert filterwheel.get_filter() == filter
            assert wait_for(lambda: "filter_change" in fired_events)
            self.assert_events()

    def test_get_filters(self, filterwheel):
        filters = filterwheel.get_filters()

        assert isinstance(filters, tuple) or isinstance(filters, list)


# ---------------------------------------------------------------------------
# Per-filter focus offsets (unit level, no bus): FilterWheelBase.set_filter
# applies the configured offset through the focuser role.
# ---------------------------------------------------------------------------

FILTERS = "U B V R I"
# I is deliberately left out: filters with no entry get no offset
FOCUS_OFFSETS = "U:-100 B:0 V:0 R:25"

FOCUSER_LOCATION = "/FakeFocuser/0"


class FakeFocuser:
    """Just enough focuser to record the relative moves it is asked for."""

    def __init__(self):
        self.position = 3500
        self.moves = []

    def move_in(self, n):
        self.moves.append(-n)
        self.position -= n

    def move_out(self, n):
        self.moves.append(+n)
        self.position += n


@pytest.fixture
def events(monkeypatch):
    """filter_change goes through the bus, which we don't have here."""
    fired = []
    monkeypatch.setattr(
        FakeFilterWheel,
        "filter_change",
        lambda self, new, old: fired.append((new, old)),
        raising=False,
    )
    return fired


@pytest.fixture
def focuser():
    return FakeFocuser()


@pytest.fixture
def chimera_log():
    """chimera's logger does not propagate to the root one, so caplog is blind."""
    messages = []

    class Recorder(logging.Handler):
        def emit(self, record):
            messages.append(record.getMessage())

    handler = Recorder()
    logger = logging.getLogger("chimera")
    logger.addHandler(handler)
    try:
        yield messages
    finally:
        logger.removeHandler(handler)


@pytest.fixture
def make_wheel(monkeypatch, events):
    def factory(focuser_proxy=None, **config):
        wheel = FakeFilterWheel()
        wheel["filters"] = FILTERS
        for key, value in config.items():
            wheel[key] = value

        if focuser_proxy is not None:
            monkeypatch.setattr(wheel, "get_proxy", lambda url: focuser_proxy)

        wheel.__start__()
        return wheel

    return factory


@pytest.fixture
def wheel(make_wheel, focuser):
    return make_wheel(
        focuser_proxy=focuser,
        focuser=FOCUSER_LOCATION,
        focus_offsets=FOCUS_OFFSETS,
    )


#
# filter wheel basics
#
class TestFilterWheel:
    def test_get_filters(self, make_wheel):
        assert make_wheel().get_filters() == FILTERS.split()

    def test_set_filter_moves_and_fires_event(self, make_wheel, events):
        wheel = make_wheel()

        assert wheel.set_filter("B")
        assert wheel.get_filter() == "B"
        assert events == [("B", "U")]

        wheel.set_filter("R")
        assert wheel.get_filter() == "R"
        assert events == [("B", "U"), ("R", "B")]

    def test_set_invalid_filter_raises(self, make_wheel):
        with pytest.raises(InvalidFilterPositionException):
            make_wheel().set_filter("Z")

    def test_no_focus_offsets_by_default(self, make_wheel):
        assert make_wheel().get_focus_offsets() == {}

    def test_offsets_without_a_focuser_are_ignored(self, make_wheel, focuser):
        # no `focuser` configured, so nothing to compensate with
        wheel = make_wheel(focuser_proxy=focuser, focus_offsets=FOCUS_OFFSETS)

        wheel.set_filter("V")

        assert focuser.moves == []

    def test_metadata(self, make_wheel):
        wheel = make_wheel()
        wheel.set_filter("V")

        keywords = dict((key, value) for key, value, _ in wheel.get_metadata(None))

        assert keywords["FILTER"] == "V"
        assert "FOCUSOFF" not in keywords


#
# focus offsets
#
class TestFilterWheelFocusOffsets:
    """
    The focuser move happens inside set_filter(), so every assertion on the
    focuser position right after set_filter() returns is also asserting that
    the offset was applied synchronously.
    """

    def test_get_focus_offsets(self, wheel):
        assert wheel.get_focus_offsets() == {"U": -100, "B": 0, "V": 0, "R": 25}

    def test_offset_applied_on_filter_change(self, wheel, focuser):
        # the wheel starts on U, so the focuser is assumed to already carry
        # U's offset: moving to V has to back those -100 steps out
        start = focuser.position

        wheel.set_filter("V")
        assert focuser.position == start + 100

        wheel.set_filter("R")
        assert focuser.position == start + 125

        wheel.set_filter("U")
        assert focuser.position == start

    def test_filter_without_offset_does_not_move(self, wheel, focuser):
        wheel.set_filter("V")
        focuser.moves.clear()

        wheel.set_filter("I")

        assert focuser.moves == []

    def test_same_offset_does_not_move(self, wheel, focuser):
        wheel.set_filter("V")
        focuser.moves.clear()

        wheel.set_filter("B")  # B and V share the same offset

        assert focuser.moves == []

    def test_no_drift_over_repeated_cycles(self, wheel, focuser):
        start = focuser.position

        for _ in range(5):
            for filter in wheel.get_filters():
                wheel.set_filter(filter)

        wheel.set_filter("U")
        assert focuser.position == start

    def test_unknown_previous_filter(self, wheel, focuser, monkeypatch):
        # a wheel that has not homed since power-up cannot report its current
        # filter (chimera-fli raises here); the offset is applied from zero
        def position_unknown():
            raise ChimeraException("wheel has not homed yet")

        monkeypatch.setattr(wheel, "get_filter", position_unknown)
        start = focuser.position

        wheel.set_filter("U")

        assert focuser.position == start - 100

    def test_metadata_reports_applied_offset(self, wheel):
        wheel.set_filter("R")

        keywords = dict((key, value) for key, value, _ in wheel.get_metadata(None))

        assert keywords["FOCUSOFF"] == 25


#
# focus offset failures
#
class TestFilterWheelFocusOffsetErrors:
    @pytest.fixture
    def unreachable(self, monkeypatch):
        def factory(**config):
            wheel = FakeFilterWheel()
            wheel["filters"] = FILTERS
            wheel["focuser"] = FOCUSER_LOCATION
            wheel["focus_offsets"] = FOCUS_OFFSETS
            for key, value in config.items():
                wheel[key] = value

            def no_such_object(url):
                raise ObjectNotFoundException(f"{url} not found.")

            monkeypatch.setattr(wheel, "get_proxy", no_such_object)
            wheel.__start__()
            return wheel

        return factory

    def test_unreachable_focuser_fails_the_filter_change(self, unreachable, events):
        wheel = unreachable()

        with pytest.raises(FocusOffsetException):
            wheel.set_filter("V")

        # the wheel itself did move and said so: the caller decides what to do
        assert wheel.get_filter() == "V"
        assert events == [("V", "U")]

    def test_focus_offset_not_required_only_logs(
        self, unreachable, events, chimera_log
    ):
        wheel = unreachable(focus_offset_required=False)

        assert wheel.set_filter("V")
        assert wheel.get_filter() == "V"
        assert events == [("V", "U")]
        assert any(
            "Could not apply a 100 focus offset" in message for message in chimera_log
        )

    def test_malformed_offsets_fail_at_startup(self, make_wheel, focuser):
        with pytest.raises(FocusOffsetException):
            make_wheel(
                focuser_proxy=focuser,
                focuser=FOCUSER_LOCATION,
                focus_offsets="U:deadbeef",
            )

    def test_offsets_for_unknown_filter_fail_at_startup(self, make_wheel, focuser):
        with pytest.raises(FocusOffsetException):
            make_wheel(
                focuser_proxy=focuser,
                focuser=FOCUSER_LOCATION,
                focus_offsets="Z:100",
            )


#
# legacy drivers
#
def test_driver_overriding_set_filter_is_warned(chimera_log):
    class LegacyFilterWheel(FakeFilterWheel):
        def set_filter(self, filter):
            pass

    # warned at construction: a legacy driver that also overrides __start__
    # without chaining up would never reach a check placed there
    LegacyFilterWheel()

    assert any("overrides set_filter()" in message for message in chimera_log)
