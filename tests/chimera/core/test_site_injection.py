# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import pytest

from chimera.core.exceptions import ObjectNotFoundException
from chimera.instruments.fakerotator import FakeRotator
from chimera.util.coord import Coord


class TestSiteInjection:
    def test_get_site_returns_shared_local_instance(self, manager):
        manager.add_class(FakeRotator, "r1", start=False)
        manager.add_class(FakeRotator, "r2", start=False)

        r1 = manager.resources.get("/FakeRotator/r1").instance
        r2 = manager.resources.get("/FakeRotator/r2").instance

        assert r1.get_site() is manager.site
        assert r2.get_site() is manager.site

    def test_site_gets_itself_injected(self, manager):
        assert manager.site.get_site() is manager.site

    def test_unregistered_object_raises(self):
        rotator = FakeRotator()
        with pytest.raises(ObjectNotFoundException):
            rotator.get_site()

    def test_site_still_reachable_over_proxy(self, manager):
        assert "/Site/lna" in manager.resources

        proxy = manager.get_proxy("/Site/0")
        assert isinstance(proxy.mjd(), float)

    def test_remote_config_change_visible_locally(self, manager):
        proxy = manager.get_proxy("/Site/0")
        proxy["latitude"] = "-30 00 00"

        assert manager.site["latitude"] == Coord.from_dms("-30 00 00")

        manager.add_class(FakeRotator, "fake", start=False)
        rotator = manager.resources.get("/FakeRotator/fake").instance
        assert rotator.get_site()["latitude"] == Coord.from_dms("-30 00 00")
