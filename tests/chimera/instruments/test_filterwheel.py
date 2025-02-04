# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.instruments.tests.base import FakeHardwareTest, RealHardwareTest

import time

from chimera.core.manager import Manager
from chimera.core.callback import callback

# hack for event  triggering asserts
FiredEvents = {}


class FilterWheelTest(object):

    FILTER_WHEEL = ""

    def assertEvents(self):

        assert "filterChange" in FiredEvents
        assert isinstance(FiredEvents["filterChange"][1], str)
        assert isinstance(FiredEvents["filterChange"][2], str)

    def setupEvents(self):

        @callback(self.manager)
        def filterChangeClbk(newFilter, oldFilter):
            FiredEvents["filterChange"] = (time.time(), newFilter, oldFilter)

        fw = self.manager.getProxy(self.FILTER_WHEEL)
        fw.filterChange += filterChangeClbk

    def test_filters(self):

        f = self.manager.getProxy(self.FILTER_WHEEL)

        filters = f.getFilters()

        for filter in filters:
            f.setFilter(filter)
            assert f.getFilter() == filter
            self.assertEvents()

    def test_get_filters(self):

        f = self.manager.getProxy(self.FILTER_WHEEL)
        filters = f.getFilters()

        assert isinstance(filters, tuple) or isinstance(filters, list)


#
# setup real and fake tests
#
class TestFakeFilterWheel(FakeHardwareTest, FilterWheelTest):

    def setup(self):

        self.manager = Manager(port=8000)

        from chimera.instruments.fakefilterwheel import FakeFilterWheel

        self.manager.addClass(
            FakeFilterWheel, "fake", {"device": "/dev/ttyS0", "filters": "U B V R I"}
        )
        self.FILTER_WHEEL = "/FakeFilterWheel/0"

        self.setupEvents()

    def teardown(self):
        self.manager.shutdown()


class TestRealFilterWheel(RealHardwareTest, FilterWheelTest):

    def setup(self):

        self.manager = Manager()

        from chimera.instruments.sbig import SBIG

        self.manager.addClass(SBIG, "sbig", {"filters": "R G B LUNAR CLEAR"})
        self.FILTER_WHEEL = "/SBIG/0"

        self.setupEvents()

    def teardown(self):
        self.manager.shutdown()
