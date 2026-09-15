# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""What an `ImageRequest` may ask for -- and what it may not.

The interesting case is `bitpix`, which used to be here. It defaulted to
uint16, nothing anywhere read it, and every frame took the dtype of whatever
array its driver happened to produce. Making it *work* would have been worse
than leaving it broken: it would have handed a remote caller the power to
narrow a 16-bit camera's frames to 8 bits, with the driver that knows better
having no standing to refuse.
"""

import pytest

from chimera.controllers.imageserver.imagerequest import ImageRequest


class TestBitpixIsNotSomethingYouCanAskFor:
    def test_a_default_request_carries_no_bitpix(self):
        assert "bitpix" not in ImageRequest()

    def test_asking_for_one_is_refused(self):
        """Loudly, rather than by being quietly dropped.

        It was silently ignored for years, which is how it went unnoticed that
        the field did nothing. A caller who believes they are choosing a pixel
        type should find out that they are not.
        """
        with pytest.raises(TypeError, match="bitpix"):
            ImageRequest(bitpix="uint16")

    def test_the_rest_of_the_request_is_untouched(self):
        """The removal took one key, not a redesign."""
        request = ImageRequest(exptime=42.0, type="dark")
        assert request["exptime"] == 42.0
        assert request["type"] == "dark"
        assert request["binning"] == "1x1"
        assert request["compress_format"] == "NO"
