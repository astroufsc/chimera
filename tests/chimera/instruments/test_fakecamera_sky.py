# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""The fake camera responds to the rest of the observatory, or it is not a simulator.

**A frame full of stars only proves rendering.** What has to be true is that the
frame depends on the instruments around it: move the focuser and the next
exposure is measurably blurrier, shut the dome and the stars go. Every routine
worth simulating -- autofocus, Bahtinov, guiding, pointing runs -- is a closed
loop through another instrument, and a camera that ignores them can only ever
test that bytes moved.

Before 2026-08-23 none of this was true. The sky came from an HTTP request for a
DSS cutout, reachable only with a telescope *and* a dome and an open aligned
slit; every other path returned `make_flat` plus dark noise. Most rigs have no
dome, so most rigs got noise.

Skips cleanly without mirage or a star catalogue, and says which is missing --
mirage builds from Rust and is not a chimera dependency, so its absence is a
normal state of the world rather than a failure.
"""

import numpy as np
import pytest

from chimera.instruments.fakecamera import FakeCamera
from chimera.instruments.fakedome import FakeDome
from chimera.instruments.fakefocuser import FakeFocuser
from chimera.instruments.faketelescope import FakeTelescope
from chimera.interfaces.telescope import TelescopePierSide

#: Small enough to render in well under a second, big enough to hold stars.
CCD = 512

# Note for anyone adding config here: chimera coerces a config **override** to
# the type of its default, so `{"rotator": None}` against a default of
# "/Rotator/0" arrives as the *string* "None" -- truthy, and then an invalid
# URL. Leave a string-defaulted option out rather than overriding it with None.
# `sky_catalog` defaults to None and so keeps NoneType, which is why that one
# can be nulled.

#: A field with stars in it, and the UT instant at which it transits the conftest
#: site (LST 0.745 h at longitude -48.52; the Sun is 51 deg down). `observatory()`
#: pins the observatory clock there, so the field is near the zenith whatever the
#: wall clock says -- before that the suite only passed for a few hours a night,
#: and failed the rest of the day with ObjectTooLowException.
RA_H, DEC_D = 0.7457, -22.006
FIELD_TRANSITS_AT = "2026-08-24 05:48:40"


def _catalog():
    """Where the Gaia container is, or None.

    mirage looks at `sky_catalog`, then `$GBX_CATALOG`, then outward from the
    running binary. The last of those cannot work from a venv, which is why the
    camera has a config option at all.
    """
    import os
    from pathlib import Path

    env = os.environ.get("GBX_CATALOG")
    if env and Path(env).exists():
        return env
    sibling = (
        Path(__file__).resolve().parents[3].parent.parent
        / "astro-ph-labs"
        / "gbx"
        / "data"
        / "catalog.gbx"
    )
    return str(sibling) if sibling.exists() else None


@pytest.fixture(scope="module")
def catalog():
    pytest.importorskip(
        "mirage", reason="mirage is not installed (`pip install mirage-sim`)"
    )
    path = _catalog()
    if path is None:
        pytest.skip(
            "no gbx catalogue found; set $GBX_CATALOG. Without it the mirage sky "
            "cannot be exercised and this file checks nothing"
        )
    return path


def observatory(manager, catalog, **camera_config):
    """A telescope, a focuser and a mirage-backed camera, pointed at stars."""
    # Site.ut() anchors its simulation clock on the first scaled call, so this
    # has to land before the telescope starts and reads the sky.
    manager.get_proxy("/Site/0")["time_start"] = FIELD_TRANSITS_AT
    manager.add_class(FakeTelescope, "tel")
    manager.add_class(FakeFocuser, "foc")
    config = {
        "sky": "mirage",
        "sky_catalog": catalog,
        "ccd_width": CCD,
        "ccd_height": CCD,
    }
    config.update(camera_config)
    manager.add_class(FakeCamera, "sky", config)
    telescope = manager.get_proxy("/FakeTelescope/tel")
    telescope.slew_to_ra_dec(RA_H, DEC_D)
    return (
        manager.get_proxy("/FakeCamera/sky"),
        telescope,
        manager.get_proxy("/FakeFocuser/foc"),
    )


def pixels(camera, tmp_path, name, exptime=2.0):
    import re

    from astropy.io import fits

    frames = camera.expose(
        exptime=exptime, frames=1, filename=str(tmp_path / f"{name}.fits")
    )
    path = re.sub(r"^file://", "", frames[0]).rsplit(",", 1)[0]
    with fits.open(path) as hdul:
        return hdul[0].data.astype(float)


def spread(frame):
    """How far the light is spread: pixels well above the background.

    A defocused star is the same flux over more pixels, so this rises as focus
    walks away from best. Deliberately not "pixels above half the peak", which
    an earlier draft used: a saturated star pins the peak, and the count then
    sits at four whatever the focus does -- it would have passed a weaker
    assertion while measuring nothing.
    """
    background = np.median(frame)
    above = frame - background
    return int((above > 5 * above.std()).sum())


class TestTheSkyRespondsToTheObservatory:
    def test_there_are_stars_at_all(self, manager, catalog, tmp_path):
        """The floor. Noise has no structure; a starfield has a bright tail."""
        camera, _tel, _foc = observatory(manager, catalog)
        frame = pixels(camera, tmp_path, "stars")
        background = np.median(frame)
        assert frame.max() > background + 200, (
            f"peak {frame.max()} is barely above the {background} background; this "
            f"looks like the flat-plus-noise fallback rather than a rendered sky"
        )

    def test_moving_the_focuser_blurs_the_next_frame(self, manager, catalog, tmp_path):
        """**The test this whole change exists for.**

        Nothing about the camera changes between these two exposures. A
        different instrument moves, and the frame has to notice -- which is the
        difference between an observatory simulator and an image source, and
        the reason autofocus can now be exercised offline at all.
        """
        camera, _tel, focuser = observatory(manager, catalog)

        focused = spread(pixels(camera, tmp_path, "focused"))
        low, high = focuser.get_range()
        focuser.move_to(int((low + high) / 2 + 600))
        defocused = spread(pixels(camera, tmp_path, "defocused"))

        print(f"\n  in focus: {focused} px above background")
        print(f"  +600 steps: {defocused} px above background")
        assert defocused > focused * 1.2, (
            f"the focuser moved 600 steps and the frame barely changed "
            f"({focused} -> {defocused} px above background). The camera is not "
            f"reading the focuser, so nothing that closes a loop through it -- "
            f"autofocus, Bahtinov -- is being simulated"
        )

    def test_moving_back_refocuses(self, manager, catalog, tmp_path):
        """And it is reversible, so it is the focus term and not a drift."""
        camera, _tel, focuser = observatory(manager, catalog)
        low, high = focuser.get_range()
        best = int((low + high) / 2)

        focuser.move_to(best + 600)
        out = spread(pixels(camera, tmp_path, "out"))
        focuser.move_to(best)
        back = spread(pixels(camera, tmp_path, "back"))
        assert back < out * 0.9, (
            f"returning to best focus did not sharpen: {out} -> {back}"
        )

    def test_a_shut_dome_lets_no_light_in(self, manager, catalog, tmp_path):
        """The dome gates the light. It does not gate the *sky source* -- those
        two were the same thing here for years, which is why a rig with no dome
        got noise."""
        manager.add_class(FakeDome, "dome", {"telescope": "/FakeTelescope/tel"})
        camera, _tel, _foc = observatory(manager, catalog)
        dome = manager.get_proxy("/FakeDome/dome")
        dome.close_slit()

        frame = pixels(camera, tmp_path, "shut")
        background = np.median(frame)
        assert frame.max() < background + 200, (
            "the dome slit is shut and stars still arrived"
        )

    def test_the_pointing_is_the_telescopes(self, manager, catalog, tmp_path):
        """Slew somewhere else and the frame changes. If it does not, the camera
        is rendering a fixed field and every pointing test is meaningless."""
        camera, telescope, _foc = observatory(manager, catalog)
        here = pixels(camera, tmp_path, "here")
        telescope.slew_to_ra_dec(RA_H + 1.5, DEC_D + 12.0)
        there = pixels(camera, tmp_path, "there")
        assert not np.array_equal(here, there), (
            "two different pointings rendered identical frames"
        )


class TestItDegradesRatherThanFailing:
    def test_a_missing_catalogue_falls_back_and_says_so(self, manager, tmp_path):
        """mirage's absence must never be a black frame with no explanation."""
        pytest.importorskip("mirage", reason="mirage is not installed")
        manager.add_class(FakeTelescope, "tel2")
        manager.add_class(
            FakeCamera,
            "nocat",
            {
                "sky": "mirage",
                "sky_catalog": "/nonexistent/catalog.gbx",
                "ccd_width": 128,
                "ccd_height": 128,
            },
        )
        camera = manager.get_proxy("/FakeCamera/nocat")
        frame = pixels(camera, tmp_path, "nocat", exptime=0.1)
        assert frame.shape == (128, 128), "a frame should still arrive"

        # Asked of the camera rather than of caplog: the warning is emitted on
        # the bus's worker thread, and an earlier draft of this assertion passed
        # when the file ran alone and failed in a full suite for that reason.
        # A recorded reason is also just better -- "why is this frame empty" is
        # answerable afterwards instead of only in whatever log was attached.
        reason = manager.resources.get(
            "/FakeCamera/nocat"
        ).instance._sky_fallback_reason
        assert reason is not None, "the fallback happened silently"
        assert "catalog" in reason, f"the reason does not name the cause: {reason}"

    def test_sky_selects_the_source_and_use_dss_gates_the_dss_path(self, manager):
        """The two config options divide cleanly, and the older one still bites.

        `sky` picks the source. `use_dss` says whether stdatu.stsci.edu may ever
        be reached -- as a source *or* as the fallback when mirage cannot
        render. A config that predates `sky` and turned DSS off must still never
        make that request, and flipping the default to mirage must not quietly
        turn it back on.
        """

        def source(name, config):
            manager.add_class(
                FakeCamera, name, {"ccd_width": 64, "ccd_height": 64, **config}
            )
            return manager.resources.get(f"/FakeCamera/{name}").instance

        assert source("default", {})._sky_source() == "mirage"
        assert source("unset", {"sky": "auto"})._sky_source() == "dss"
        assert (
            source("unset_off", {"sky": "auto", "use_dss": False})._sky_source()
            == "none"
        )
        assert source("asked", {"sky": "dss"})._sky_source() == "dss"
        # `None` is not how you defer: chimera coerces it to the string "None"
        # against a string default, which reads as "none" -- no sky at all.
        assert source("nulled", {"sky": None})._sky_source() == "none"

        # The one that matters: DSS asked for and forbidden is not DSS.
        refused = source("refused", {"sky": "dss", "use_dss": False})
        assert refused._sky_source() == "none"
        assert not refused._dss_allowed()

        # And mirage never reaches for DSS behind a `use_dss = False`.
        assert not source(
            "no_fallback", {"sky": "mirage", "use_dss": False}
        )._dss_allowed()
        assert source("with_fallback", {"sky": "mirage"})._dss_allowed()


class TestTheRotatorReachesTheRenderer:
    """The rotator is an instrument like any other, and the frame must follow it.

    It is also the one place where *how* the angle is applied matters as much as
    whether it is. This class applied it with `_rotate` -- nearest-neighbour
    resampling with zero-filled corners -- which smears every PSF and leaves a
    WCS that no longer describes the frame. For an image whose whole purpose is
    to be plate solved, that is the wrong mechanism, so mirage grew a
    `rotator_pa` argument and renders at the angle instead.

    The corners are how you tell the two apart, and that is what makes this
    testable rather than a matter of trust.
    """

    def rig(self, manager, catalog, angle):
        from chimera.instruments.fakerotator import FakeRotator

        manager.add_class(FakeRotator, "rot")
        camera, _tel, _foc = observatory(manager, catalog, rotator="/FakeRotator/rot")
        manager.get_proxy("/FakeRotator/rot").move_to(angle)
        return camera

    def test_the_frame_follows_the_rotator(self, manager, catalog, tmp_path):
        camera = self.rig(manager, catalog, 0.0)
        straight = pixels(camera, tmp_path, "pa0")
        manager.get_proxy("/FakeRotator/rot").move_to(35.0)
        turned = pixels(camera, tmp_path, "pa35")
        assert not np.array_equal(straight, turned), (
            "the rotator moved 35 degrees and the frame did not change"
        )

    def test_it_is_rendered_at_the_angle_not_resampled(
        self, manager, catalog, tmp_path
    ):
        """**The corners say which mechanism ran.**

        `_rotate` fills everything that rotated in from outside the frame with
        zeros, so a resampled 35-degree frame has four large triangles of exact
        zero. A frame rendered at the angle has sky in its corners like any
        other. Zero is unmistakable here -- the detector's own offset puts the
        background at ~500 ADU, so nothing legitimate is near it.
        """
        camera = self.rig(manager, catalog, 35.0)
        frame = pixels(camera, tmp_path, "corners")
        corner = 48
        patches = [
            frame[:corner, :corner],
            frame[:corner, -corner:],
            frame[-corner:, :corner],
            frame[-corner:, -corner:],
        ]
        zeros = sum(int((p == 0).sum()) for p in patches)
        assert zeros == 0, (
            f"{zeros} exactly-zero pixels in the corners of a 35-degree frame. That "
            f"is the signature of `_rotate` resampling a rendered image -- the "
            f"rotator angle is being applied twice, or applied in the wrong place, "
            f"and every PSF in this frame has been through nearest-neighbour "
            f"interpolation on the way"
        )


def frame(camera, tmp_path, name, **kwargs):
    """Take one exposure and return `(header, data)` straight off disk.

    Deliberately not `pixels()`, which casts to float for arithmetic: these
    tests are about the type the file was written in, and that cast would hide
    exactly what they exist to check.
    """
    import re

    from astropy.io import fits

    frames = camera.expose(frames=1, filename=str(tmp_path / f"{name}.fits"), **kwargs)
    path = re.sub(r"^file://", "", frames[0]).rsplit(",", 1)[0]
    with fits.open(path) as hdul:
        return hdul[0].header, hdul[0].data.copy()


class TestTheCameraOwnsItsPixelType:
    """A frame is uint16 because the camera is, not because anyone asked.

    BITPIX used to be a field on `ImageRequest` that nothing ever read, so the
    type on disk was whatever numpy array a driver happened to hand over -- and
    this one handed over float32 on every path, including an `.astype(float32)`
    that undid the uint16 mirage had just produced. Every frame came out
    BITPIX -32, twice the size it needed to be, and RICE-compressed lossily.
    """

    def test_a_sky_frame_is_uint16(self, manager, catalog, tmp_path):
        camera, _tel, _foc = observatory(manager, catalog)
        header, data = frame(camera, tmp_path, "sky", exptime=2.0)
        assert header["BITPIX"] == 16
        # FITS has no unsigned 16-bit type; this pair *is* uint16 on disk.
        assert header["BZERO"] == 32768
        assert data.dtype == np.uint16

    @pytest.mark.parametrize("frame_type", ["dark", "flat", "bias"])
    def test_calibration_frames_are_uint16_too(
        self, manager, catalog, tmp_path, frame_type
    ):
        camera, _tel, _foc = observatory(manager, catalog)
        header, data = frame(camera, tmp_path, frame_type, exptime=1.0, type=frame_type)
        assert header["BITPIX"] == 16
        assert data.dtype == np.uint16

    def test_the_type_survives_a_camera_with_no_observatory(
        self, manager, catalog, tmp_path
    ):
        """No telescope, no dome, no focuser -- the fallback paths count too."""
        manager.add_class(
            FakeCamera,
            "alone",
            {"sky": "none", "ccd_width": CCD, "ccd_height": CCD},
        )
        camera = manager.get_proxy("/FakeCamera/alone")
        header, data = frame(camera, tmp_path, "alone", exptime=1.0)
        assert header["BITPIX"] == 16
        assert data.dtype == np.uint16


class TestCalibrationFramesComeFromTheSameDetector:
    """A dark has to subtract off the frame it belongs to.

    These used to be `make_dark`/`make_flat` -- a different noise model from the
    one rendering the sky, which is the one thing a calibration frame must not
    be. They now come from mirage's detector, the same chip with the same read
    noise, dark current and temperature as every object frame.
    """

    def test_a_bias_is_the_read_chain_and_nothing_else(
        self, manager, catalog, tmp_path
    ):
        camera, _tel, _foc = observatory(manager, catalog)
        _h, bias = frame(camera, tmp_path, "bias", exptime=0.0, type="bias")
        # mirage's offset, and read noise either side of it -- not a flat field
        # scaled down, which is what the fallback used to hand back.
        assert 400 < np.median(bias) < 700
        assert bias.std() < 20

    def test_dark_current_accumulates_with_time(self, manager, catalog, tmp_path):
        """The property that makes a dark worth taking at all."""
        camera, _tel, _foc = observatory(manager, catalog)
        _h, bias = frame(camera, tmp_path, "d_bias", exptime=0.0, type="bias")
        _h, long_dark = frame(camera, tmp_path, "d_long", exptime=30.0, type="dark")

        assert np.median(long_dark) > np.median(bias)
        # Hot pixels run away far faster than the median does; a 30 s dark on a
        # chip sitting at +20 C has some near saturation.
        assert long_dark.max() > 10 * bias.max()

    def test_a_flat_is_a_high_signal_frame(self, manager, catalog, tmp_path):
        """**The `/1000` regression gate.**

        The old fallback divided a ~1000 ADU flat by 1000, which was survivable
        only while frames were float: as the integer ADU this camera now writes,
        it would be a field of literal 1s. A flat is meant to be up near full
        well, where photon statistics are good enough to divide by.
        """
        camera, _tel, _foc = observatory(manager, catalog)
        _h, flat = frame(camera, tmp_path, "flat", exptime=1.0, type="flat")
        assert np.median(flat) > 20000
        assert flat.max() < 65535, (
            "a flat this close to saturation cannot be divided by"
        )

    def test_they_need_no_sky_no_telescope_and_no_dome(self, manager, tmp_path):
        """**`sky` picks where the sky comes from, and a bias has no sky in it.**

        So `sky = "none"` does not disable the detector -- it says not to render
        stars. A camera alone on a bench, with nothing pointed anywhere, still
        takes a bias and a flat that look like its own chip. Gating these on
        `sky` would have meant a rig that renders no sky also loses its
        calibration model, for no physical reason.
        """
        # The 400-700 ADU pedestal and the half-well flat are mirage's detector;
        # without it the fallback is the old synthetic frame with no bias level.
        pytest.importorskip("mirage", reason="mirage is not installed")
        manager.add_class(
            FakeCamera,
            "bench",
            {"sky": "none", "ccd_width": CCD, "ccd_height": CCD},
        )
        camera = manager.get_proxy("/FakeCamera/bench")

        _h, bias = frame(camera, tmp_path, "bench_bias", exptime=0.0, type="bias")
        _h, flat = frame(camera, tmp_path, "bench_flat", exptime=1.0, type="flat")

        assert 400 < np.median(bias) < 700
        assert np.median(flat) > 20000

    def test_a_calibration_frame_is_not_rotated(self, manager, catalog, tmp_path):
        """There is no sky in a dark, so there is no angle to render it at.

        `_rotate` zero-fills whatever turns in from outside the frame, so a
        resampled 35-degree frame has four unmistakable triangles of exact zero
        -- unmistakable because the detector's own offset puts even a bias at
        ~500 ADU and nothing legitimate goes near zero.
        """
        from chimera.instruments.fakerotator import FakeRotator

        manager.add_class(FakeRotator, "calrot")
        camera, _tel, _foc = observatory(
            manager, catalog, rotator="/FakeRotator/calrot"
        )
        manager.get_proxy("/FakeRotator/calrot").move_to(35.0)

        _h, dark = frame(camera, tmp_path, "calrot", exptime=1.0, type="dark")

        assert int((dark == 0).sum()) == 0, (
            "exactly-zero pixels in a dark taken with the rotator at 35 degrees: "
            "`_rotate` resampled a calibration frame, which only smears its noise "
            "and blanks its corners"
        )


class TestThePointingStateReachesTheRenderer:
    """`MNTSIDE` on the frame, from the telescope, through the Python module.

    This is a three-layer path and every layer has been wrong once. mirage's
    Rust tests call `true_pointing` directly, so they missed a bug where a
    beyond-the-pole command silently rendered a normal frame; its Python gates
    all drive the CLI, so the pyo3 binding -- which is the only layer chimera
    ever touches -- had no coverage at all. FakeTelescope reported UNKNOWN
    forever, so nothing downstream could have noticed either way.
    """

    def _header(self, camera, tmp_path, name):
        import re

        from astropy.io import fits

        frames = camera.expose(
            exptime=1.0, frames=1, filename=str(tmp_path / f"{name}.fits")
        )
        path = re.sub(r"^file://", "", frames[0]).rsplit(",", 1)[0]
        with fits.open(path) as hdul:
            return dict(hdul[0].header)

    def test_the_frame_records_which_state_the_mount_was_in(
        self, manager, catalog, tmp_path
    ):
        camera, telescope, _foc = observatory(manager, catalog)
        header = self._header(camera, tmp_path, "side")
        assert header.get("MNTSIDE") in ("normal", "beyond"), (
            "the frame does not say which pointing state produced it, so a "
            "pointing fit cannot know whether CH and NP reversed"
        )
        assert header["MNTSIDE"] == (
            "beyond"
            if telescope.get_mount_side() == TelescopePierSide.BEYOND
            else "normal"
        ), "the frame disagrees with the telescope that produced it"

    def test_a_meridian_crossing_changes_the_state(self, manager, catalog, tmp_path):
        """Both branches must be reachable, or a survey covers one of two."""
        _camera, telescope, _foc = observatory(manager, catalog)
        site = telescope.get_site()
        lst_h = float(site.lst_in_rads()) * 12.0 / 3.141592653589793

        seen = set()
        for offset_h in (-3.0, +3.0):
            telescope.slew_to_ra_dec((lst_h - offset_h) % 24.0, DEC_D)
            seen.add(str(telescope.get_mount_side()))

        assert seen == {"NORMAL", "BEYOND"}, (
            f"crossing the meridian gave {seen}, so one branch of "
            f"PointingModel::apply is exercised by nothing"
        )
