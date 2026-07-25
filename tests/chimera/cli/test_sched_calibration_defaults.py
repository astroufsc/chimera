# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.cli.sched import ChimeraSched

implied = ChimeraSched._calibration_defaults


class TestCalibrationDefaults:
    def test_bias_gets_zero_exptime_and_closed_shutter(self):
        assert implied({"action": "expose", "frames": 10, "image_type": "BIAS"}) == {
            "exptime": 0,
            "shutter": "CLOSE",
        }

    def test_dark_gets_closed_shutter_but_keeps_exptime(self):
        assert implied(
            {"action": "expose", "frames": 10, "exptime": 100, "image_type": "DARK"}
        ) == {"shutter": "CLOSE"}

    def test_explicit_shutter_wins_so_light_darks_still_work(self):
        assert (
            implied(
                {
                    "action": "expose",
                    "exptime": 100,
                    "shutter": "OPEN",
                    "image_type": "DARK",
                }
            )
            == {}
        )

    def test_explicit_bias_exptime_wins(self):
        assert implied({"action": "expose", "exptime": 2, "image_type": "BIAS"}) == {
            "shutter": "CLOSE"
        }

    def test_image_type_is_case_insensitive(self):
        assert implied({"action": "expose", "image_type": "bias"}) == {
            "exptime": 0,
            "shutter": "CLOSE",
        }

    def test_object_and_flat_are_untouched(self):
        assert implied({"action": "expose", "image_type": "OBJECT"}) == {}
        assert implied({"action": "expose", "image_type": "FLAT"}) == {}
        assert implied({"action": "expose"}) == {}
