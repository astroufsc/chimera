# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import msgspec

from chimera.core.chimera_config import ChimeraConfig


def _parse(text):
    return ChimeraConfig(text, decoder=msgspec.yaml.decode)


class TestSiteConfigName:
    def test_configured_name_reaches_site(self):
        # `name` must survive as a config value so it shows up in the SITE header (#231)
        cfg = _parse(
            """
            site:
              name: Swope
              latitude: "-29:00:00"
            """
        )
        url, conf = next(iter(cfg.sites.items()))
        assert url.name == "Swope"
        assert conf["name"] == "Swope"

    def test_default_name_when_omitted(self):
        cfg = _parse('site:\n  latitude: "-29:00:00"\n')
        _, conf = next(iter(cfg.sites.items()))
        assert conf["name"] == "UFSC"
