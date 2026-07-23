# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import time

import pytest

from chimera.instruments.fakefilterwheel import FakeFilterWheel

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
