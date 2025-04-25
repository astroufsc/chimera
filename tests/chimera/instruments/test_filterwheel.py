# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from .base import FakeHardwareTest, RealHardwareTest

import time

from chimera.core.manager import Manager

# hack for event triggering asserts
fired_events = {}


class FilterWheelTest(object):

    filter_wheel = ""

    def assert_events(self):

        assert "filter_change" in fired_events
        assert isinstance(fired_events["filter_change"][1], str)
        assert isinstance(fired_events["filter_change"][2], str)

    def setup_events(self):

        def filter_change_clbk(new_filter, old_filter):
            fired_events["filter_change"] = (time.time(), new_filter, old_filter)

        fw = self.manager.get_proxy(self.filter_wheel)
        fw.filter_change += filter_change_clbk

    def test_filters(self):

        f = self.manager.get_proxy(self.filter_wheel)

        filters = f.get_filters()

        for filter in filters:
            f.set_filter(filter)
            assert f.get_filter() == filter
            self.assert_events()

    def test_get_filters(self):

        f = self.manager.get_proxy(self.filter_wheel)
        filters = f.get_filters()

        assert isinstance(filters, tuple) or isinstance(filters, list)


#
# setup real and fake tests
#
class TestFakeFilterWheel(FakeHardwareTest, FilterWheelTest):

    def setup(self):

        self.manager = Manager(port=8000)

        from chimera.instruments.fakefilterwheel import FakeFilterWheel

        self.manager.add_class(
            FakeFilterWheel, "fake", {"device": "/dev/ttyS0", "filters": "U B V R I"}
        )
        self.filter_wheel = "/FakeFilterWheel/0"

        self.setup_events()

    def teardown(self):
        self.manager.shutdown()


class TestRealFilterWheel(RealHardwareTest, FilterWheelTest):

    def setup(self):

        self.manager = Manager()

        from chimera.instruments.sbig import SBIG

        self.manager.add_class(SBIG, "sbig", {"filters": "R G B LUNAR CLEAR"})
        self.filter_wheel = "/SBIG/0"

        self.setup_events()

    def teardown(self):
        self.manager.shutdown()
