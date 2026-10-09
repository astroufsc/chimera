# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

"""The fake camera, which is really the observatory simulator.

**It is not an image source.** Move the focuser and the next frame is blurrier;
change the filter and the photometry moves; shut the dome and the stars go. That
is the whole point of it: every routine worth simulating -- autofocus V-curves,
Bahtinov masks, guiding, pointing runs, polar alignment -- is a closed loop
through *another* instrument, and none of them can be exercised against a frame
that does not respond to it.

For most of this file's life it could not do any of that. The sky came from an
HTTP request to `stdatu.stsci.edu` for a DSS cutout, reachable only when a
telescope *and* a dome were present and the slit open and aligned; every other
path fell through to `make_flat` plus dark noise. Without a dome -- which is most
test rigs -- the simulated camera returned noise, and nothing in the frame
depended on any other instrument.

The sky now comes from **mirage**, an offline CCD simulator written for chimera:
real Gaia DR3 stars at the commanded pointing, through a parameterized optic,
atmosphere, mount and detector. The division of labour is mirage's own, and it is
why this class has to do the gathering:

    mirage holds no session state. Chimera's fake devices own everything
    commanded -- pointing, guide corrections, focuser position, cooler, filter --
    while autonomous physics (mount error, ambient temperature, seeing) are
    seeded deterministic functions of the exposure timestamp.

So there are two layers here. `_mirage_config` synthesizes mirage's TOML from
**static** instrument configuration, once, and caches it. `_sky_state` gathers
**live** state from the sibling instruments on every single exposure and passes
it to `expose()`.

Synthesizing `[camera]` from this class's own geometry is not tidiness: it gives
the plate scale exactly one source. Letting mirage and chimera each hold their
own would not fail, it would render frames that *solve wrongly*.

**Calibration frames come from the same detector.** Darks, flats and biases go
to mirage's `dark()`, `flat()` and `bias()` rather than to `make_dark` and
`make_flat`, because a calibration frame drawn from a different noise model than
the frames it calibrates is the one thing it must not be. They take
`_detector_state` rather than `_sky_state`: a bias has no pointing, so it needs
no telescope and no dome, and it is not gated on `sky` either -- that option
picks where the *sky* comes from, and there is no sky in a dark.

**BITPIX belongs to this camera, not to whoever asked for the frame.** Every
path here computes in float (noise is float, and `make_dark`/`make_flat` cannot
fill an integer buffer in place), so `_readout` narrows to uint16 once, at the
end, for all of them. The pixel type used to be a field on `ImageRequest` that
nothing read -- see that class for why making it work would have been worse than
deleting it.

**mirage is optional and its absence is named.** It builds from Rust through
maturin, so it is not a chimera dependency at all -- install `mirage-sim` beside
chimera to render the sky; `pip install chimera` must not require a toolchain to
render frames most installs never ask for. Missing module, missing catalogue, or a render that raises all
degrade to the DSS path and then to flat-plus-noise, each with a log line saying
which and why. A black frame with no explanation is the one outcome worth
engineering against.
"""

import datetime as dt
import os
import random
import shutil
import time
import urllib.parse
import urllib.request

import numpy as np
from astropy.io import fits

from chimera.core.lock import lock
from chimera.instruments.camera import CameraBase
from chimera.interfaces.camera import CameraFeature, CameraStatus, ReadoutMode
from chimera.interfaces.rotator import Rotator
from chimera.interfaces.telescope import TelescopePierSide
from chimera.util.position import Epoch, Position


class FakeCamera(CameraBase):
    __config__ = {
        #: Where the sky comes from: "mirage", "dss" or "none".
        #:
        #: `use_dss` below is honoured for compatibility and is what this used
        #: to be: it selects "dss" when this is left unset. Setting `sky`
        #: explicitly wins; `sky = "auto"` defers to it entirely.
        #:
        #: The default became "mirage" on 2026-08-22. Before that it was unset,
        #: which meant DSS -- and DSS meant, in practice, flat plus dark noise,
        #: because the download needed a dome with an open aligned slit and most
        #: rigs have no dome at all. Anything that cannot reach mirage still
        #: falls back to exactly what it did before, with a log line saying why.
        "sky": "mirage",
        #: The gbx container mirage draws stars from. `None` lets gbx discover
        #: one ($GBX_CATALOG, then outward from the running binary). A venv
        #: install is nowhere near a sibling checkout, so this is usually how a
        #: development rig points at one.
        "sky_catalog": None,
        #: A mirage TOML to start from. `None` synthesizes the whole thing from
        #: the instruments; a path here is merged over that, which is how a real
        #: optic gets its obstruction, throughput and PSF model.
        "sky_config": None,
        #: The PSF model: "fourier" or "moffat".
        #:
        #: **"moffat" cannot see the focuser.** It is a fast analytic profile
        #: and defocus does not enter it, so a frame rendered with it is
        #: identical at best focus and 600 microns out -- measured here, not
        #: assumed. Choosing it silently disables every routine that closes a
        #: loop through the focuser, which is most of the reason this camera
        #: renders a real sky at all. "fourier" is physical optics, costs about
        #: 0.1 s a frame at 512 px, and is the default for that reason.
        "sky_psf": "fourier",
        #: Focuser travel per step, microns. The focuser interface reports steps
        #: and mirage wants microns, and nothing in chimera carries the ratio.
        "sky_um_per_step": 1.0,
        #: Injected periodic error, arcsec and seconds. Zero is a perfect mount.
        #: This is what makes a tracking trace gradeable against known truth --
        #: 287.2 s is one AM5 motor revolution, 430.8 s one strain-wave cycle.
        "sky_pe_amplitude": 0.0,
        "sky_pe_period": 287.2,
        "use_dss": True,
        "ccd_width": 512,
        "ccd_height": 512,
        "rotator": "/Rotator/0",
    }

    def __init__(self):
        CameraBase.__init__(self)

        self.__cooling = False

        self.__temperature = 20.0
        self.__setpoint = 0
        self.__last_frame_start = 0
        self.__is_fanning = False

        # The synthesized mirage config, what it was synthesized from, and the
        # simulator built on it. All three move together; see `_mirage_config`.
        self._mirage_key = None
        self._mirage_text = None
        self._mirage_sim = None
        #: Why the sky fell back, or None if it did not. Logged as well, but
        #: kept here because a log line emitted on the bus's worker thread is
        #: awkward for a caller -- or a test -- to ask about afterwards, and
        #: "why is this frame empty" is exactly the question worth answering.
        self._sky_fallback_reason = None

        # my internal CCD code
        self._my_adc = 1 << 2
        self._my_readout_mode = 1 << 3

        self._adcs = {"12 bits": self._my_adc}

        self._binnings = {"1x1": self._my_readout_mode}

        self._binning_factors = {"1x1": 1}

        self._supports = {
            CameraFeature.TEMPERATURE_CONTROL: True,
            CameraFeature.PROGRAMMABLE_GAIN: False,
            CameraFeature.PROGRAMMABLE_OVERSCAN: False,
            CameraFeature.PROGRAMMABLE_FAN: False,
            CameraFeature.PROGRAMMABLE_LEDS: True,
            CameraFeature.PROGRAMMABLE_BIAS_LEVEL: False,
        }

        readout_mode = ReadoutMode()
        readout_mode.mode = 0
        readout_mode.gain = 1.0
        readout_mode.width = 1024
        readout_mode.height = 1024
        readout_mode.pixel_width = 9.0
        readout_mode.pixel_height = 9.0

        self._readout_modes = {self._my_readout_mode: readout_mode}

    @staticmethod
    def _rotate(pix, angle):
        """
        Rotate an image counter-clockwise about its center by ``angle``
        degrees, keeping the original shape. Nearest-neighbour sampling is
        enough for the fake camera and avoids a scipy dependency.
        """
        a = np.deg2rad(-angle)
        h, w = pix.shape
        cy, cx = (h - 1) / 2, (w - 1) / 2
        y, x = np.indices((h, w))
        xs = np.cos(a) * (x - cx) + np.sin(a) * (y - cy) + cx
        ys = -np.sin(a) * (x - cx) + np.cos(a) * (y - cy) + cy
        xi = np.rint(xs).astype(int)
        yi = np.rint(ys).astype(int)
        ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
        out = np.zeros_like(pix)
        out[ok] = pix[yi[ok], xi[ok]]
        return out

    def __start__(self):
        self["camera_model"] = "Fake Cameras Inc."
        self["ccd_model"] = "Fake CCDs Inc."

        self.set_hz(2)

    def control(self):
        if self.is_cooling():
            if self.__temperature > self.__setpoint:
                self.__temperature -= 0.5

        return True

    def _observatory_clock(self):
        """The observatory's own notion of now, and how fast it is running.

        `Site` already owns a fast-forward simulation clock -- `time_speedup`
        and `time_start`, with `Site.ut()` returning
        `time_start + (wall_now - wall_at_first_call) * time_speedup`. Its
        docstring says the point is that "the whole observatory (scheduler,
        robobs, sky flats, FITS timestamps) advances through a night in
        compressed real time".

        FITS timestamps were the part that did not. This camera stamped
        `dt.datetime.now()`, so with a scaled site it would render frames at the
        wall clock while the scheduler and the ephemeris ran on the simulated
        one -- the two drifting apart with no sign of it in the data. Asking Site
        closes that, and means there is one clock rather than two.

        Falls back to the wall clock and unity if there is no site to ask, so a
        camera constructed outside a manager still works.
        """
        try:
            site = self.get_site()
            speedup = float(site["time_speedup"])
            return site.ut(), (speedup if speedup > 0 else 1.0)
        except Exception:
            return dt.datetime.now(dt.UTC), 1.0

    def _expose(self, image_request):
        self.expose_begin(image_request)

        status = CameraStatus.OK

        t = 0
        self.__last_frame_start, speedup = self._observatory_clock()

        # The wait is the only thing that shrinks. `exptime` still means what it
        # says -- the renderer uses it for signal, for trailing and for the
        # mount's time-dependent error -- and the timestamps above and below are
        # the simulated ones, so a compressed run produces the frames a
        # real-time run would have produced. At `time_speedup = 1` this is
        # exactly the loop it has always been.
        #
        # Worth knowing: the sleep is most of an offline run. Measured on a
        # mirage-backed rig, a 2 s exposure costs 2.45 s per frame, of which
        # 2.0 s is this loop and 0.45 s is render, FITS write and readout.
        while t < image_request["exptime"]:
            # [ABORT POINT]
            if self.abort.is_set():
                status = CameraStatus.ABORTED
                break

            # A tenth of a SIMULATED second. The loop is kept rather than
            # collapsed into one sleep so an abort is still noticed promptly.
            time.sleep(0.1 / speedup)
            t += 0.1

        time.sleep(0.1 / speedup)  # simulate shutter close time
        self.expose_complete(image_request, status)

    def make_dark(self, shape, dtype, exptime):
        ret = np.zeros(shape, dtype=dtype)
        # Taken from specs for KAF-1603ME as found in ST-8XME
        # normtemp is now in ADU/pix/sec
        normtemp = ((10 * 2 ** ((self.__temperature - 25) / 6.3)) * exptime) / 2.3
        ret += normtemp + np.random.random(shape)  # +/- 1 variance in readout
        return ret

    def make_flat(self, shape, dtype):
        """
        Flat is composition of:
         - a normal distribution of mean=1000, sigma=1
         - plus a pixel sensitivity constant, which is axis dependent
         - plus a bad region with different mean level
        """

        iadd = 15.0 // shape[0]
        jadd = 10.0 // shape[1]

        badlevel = 0

        badareai = shape[0] // 2
        badareaj = shape[1] // 2

        # this array is only to make sure we create our array
        # with the right dtype
        ret = np.zeros(shape, dtype=dtype)

        ret += np.random.normal(1000, 1, shape)
        ret += np.fromfunction(lambda i, j: i * iadd - j * jadd, shape)

        ret[badareai:, badareaj:] += badlevel

        return ret

    # --- the sky ---------------------------------------------------------
    #
    # See the module docstring. Two layers: a config synthesized once from
    # static instrument configuration, and live state gathered every exposure.

    def _sky_source(self):
        """ "mirage", "dss" or "none" -- which source renders the sky.

        `use_dss` predates this and the two divide cleanly: **`sky` selects the
        source, `use_dss` gates the DSS path.** So `use_dss = False` still means
        what it always did -- never reach for stdatu.stsci.edu -- both as a
        source and as the fallback when mirage cannot render, and a config that
        set only `use_dss` still gets what it asked for after the default moved
        to mirage.

        `sky = "auto"` defers entirely. **Not `None`**: chimera coerces a config
        override to the type of its default, so `None` against a string default
        arrives as the *string* `"None"`, which lowercases to a perfectly good
        `"none"` and means no sky at all. That is a fair reading of what someone
        wrote, so it is left to mean that, and "auto" is the word for deferring.
        """
        chosen = (self["sky"] or "auto").strip().lower()
        if chosen == "auto":
            return "dss" if self["use_dss"] else "none"
        if chosen == "dss" and not self["use_dss"]:
            return "none"
        if chosen in ("mirage", "dss", "none"):
            return chosen
        return "dss" if self["use_dss"] else "none"

    def _dss_allowed(self):
        """Whether the DSS path may run, as a source or as a fallback.

        Separate from `_sky_source` because mirage failing must not smuggle a
        network request past a `use_dss = False` that was written precisely to
        forbid one.
        """
        return bool(self["use_dss"]) and self._sky_source() != "none"

    def _proxy(self, location):
        """A sibling instrument, or None. Absence is normal, not an error."""
        try:
            proxy = self.get_proxy(location)
            return proxy if proxy.ping() else None
        except Exception:
            return None

    def _detector_state(self, image_request, binning_factor):
        """What the detector alone contributes, with nothing pointed anywhere.

        Split out of `_sky_state` because a calibration frame has no pointing:
        a bias is the chip and its electronics and nothing else, so asking a
        telescope where it is looking in order to take one would invent a
        dependency the physics does not have.
        """
        return {
            "exptime": float(image_request["exptime"]),
            "binning": int(binning_factor),
            "temp_c": self.get_temperature(),
            "seed": 0,
        }

    def _sky_state(self, telescope, image_request, binning_factor):
        """Live observatory state, gathered fresh for this exposure.

        **This is the method that makes it a simulator.** Everything here is
        read at exposure time from whatever instrument owns it, so a focuser
        that moved between frames shows up in the next one. Every source is
        optional: a missing focuser means `focus=None`, which mirage reads as
        in focus -- not an error, and not a black frame.
        """
        state = self._detector_state(image_request, binning_factor)

        # The pointing state, read BEFORE the position and not after it.
        #
        # **Ordering is load-bearing.** Every proxy round-trip between
        # reading the mount's position and opening the shutter is time for
        # the mount to move, and the frame is then rendered somewhere the
        # caller's recorded pose does not describe. A kepler survey measured
        # 0.68 arcsec of declination-shaped residual on a NULL run from
        # exactly this ordering, against 0.03 with the position read last.
        #
        # The rule: the position is the LAST thing read before rendering.
        # Anything else the frame needs is read first.
        #
        # From the telescope already in hand. It is the
        # GEOMETRIC one -- Wallace's normal/beyond -- because that is what
        # mirage's mount model means by `side`, and it is not the same quantity
        # as ASCOM's mechanical EAST/WEST. A telescope too old to answer leaves
        # it at `normal`, which is what every frame was before this existed.
        #
        # `==` and not `is`: across a bus this arrives as a plain `str`.
        try:
            side = telescope.get_mount_side()
            if side == TelescopePierSide.BEYOND:
                state["side"] = "beyond"
            elif side == TelescopePierSide.NORMAL:
                state["side"] = "normal"
        except Exception as e:
            self.log.debug(f"telescope would not report its pointing state: {e}")

        ra, dec = telescope.get_position_ra_dec()
        # chimera carries RA in hours; mirage, like every catalogue, wants degrees.
        state["ra"] = float(ra) * 15.0
        state["dec"] = float(dec)

        focuser = self._proxy("/Focuser/0")
        if focuser is not None:
            try:
                state["focus"] = float(focuser.get_position())
            except Exception as e:
                self.log.debug(f"focuser present but would not report position: {e}")

        wheel = self._proxy("/FilterWheel/0")
        if wheel is not None:
            try:
                state["filter"] = str(wheel.get_filter())
            except Exception as e:
                self.log.debug(f"filter wheel present but would not report: {e}")

        weather = self._proxy("/WeatherStation/0")
        if weather is not None:
            for key, call in (("ambient_c", "temperature"), ("seeing", "seeing")):
                try:
                    value = getattr(weather, call)()
                    # The weather interface returns a value-with-unit for some
                    # stations and a bare float for others.
                    state[key] = float(getattr(value, "value", value))
                except Exception as e:
                    self.log.debug(f"weather station has no usable {call}: {e}")

        # **The rotator, and it goes to mirage rather than to numpy.** This class
        # has always applied it with `_rotate`, a nearest-neighbour resample with
        # zero-filled corners -- which smears every PSF in the frame and leaves a
        # WCS that no longer describes it. That is the wrong mechanism for an
        # image whose whole purpose is to be plate solved, so mirage renders at
        # the angle instead (`rotator_pa`, added there for this) and `_readout`
        # skips the resample for rendered frames.
        rotator = self._proxy(self["rotator"]) if self["rotator"] else None
        if rotator is not None:
            try:
                state["rotator_pa"] = float(rotator.get_position())
            except Exception as e:
                self.log.debug(f"rotator present but would not report position: {e}")

        guider = self._proxy("/Autoguider/0")
        if guider is not None:
            try:
                offset = guider.get_offset()
                state["guide_ra"], state["guide_dec"] = (
                    float(offset[0]),
                    float(offset[1]),
                )
            except Exception as e:
                self.log.debug(f"autoguider present but reports no offset: {e}")

        return state

    def _mirage_config(self):
        """mirage's TOML, synthesized from the instruments and cached.

        Static only -- geometry, optics, site, the mount's injected error. Live
        state never comes through here; it goes to `expose()` per frame. The
        cache key is what went into it, so a reconfigured observatory rebuilds
        and a busy one does not.
        """
        telescope = self._proxy("/Telescope/0")
        focuser = self._proxy("/Focuser/0")
        site = self.get_site()

        aperture, focal_length, optics = 100.0, 1000.0, "Newtonian"
        if telescope is not None:
            try:
                aperture = float(telescope["aperture"])
                focal_length = float(telescope["focal_length"]) * float(
                    telescope["focal_reduction"] or 1.0
                )
                optics = str(telescope["optics"])
            except Exception as e:
                self.log.debug(f"telescope config unreadable, using defaults: {e}")

        # Best focus is the middle of the focuser's travel, which is where
        # `FakeFocuser` starts -- so a fresh observatory is in focus and moving
        # the focuser defocuses it. Getting this from the instrument rather than
        # from a constant is what makes that true for a real focuser too.
        best_position = 0.0
        if focuser is not None:
            try:
                low, high = focuser.get_range()
                best_position = (float(low) + float(high)) / 2.0
            except Exception as e:
                self.log.debug(f"focuser reports no range: {e}")

        width, height = self.get_physical_size()
        pixel_um, _ = self.get_pixel_size()

        key = (
            aperture,
            focal_length,
            optics,
            best_position,
            width,
            height,
            pixel_um,
            site.latitude_in_degs(),
            site.longitude_in_degs(),
            site.altitude_in_m(),
            self["sky_um_per_step"],
            self["sky_pe_amplitude"],
            self["sky_pe_period"],
            self["sky_config"],
            self["sky_psf"],
        )
        if getattr(self, "_mirage_key", None) == key and self._mirage_text is not None:
            return self._mirage_text

        base = ""
        if self["sky_config"]:
            base = open(self["sky_config"]).read() + "\n"

        mount = ""
        if self["sky_pe_amplitude"]:
            mount = (
                '[mount]\nmodel = "parametric"\n'
                f"pe_amplitude_arcsec = {float(self['sky_pe_amplitude'])}\n"
                f"pe_period_s = {float(self['sky_pe_period'])}\n"
            )

        text = (
            base
            + f"""
[telescope]
focal_length_mm = {focal_length}
aperture_mm = {aperture}

[camera]
type = "cmos"
width = {int(width)}
height = {int(height)}
pixel_um = {float(pixel_um)}

[site]
name = "{site["name"]}"
lat = {site.latitude_in_degs()}
lon = {site.longitude_in_degs()}
alt_m = {site.altitude_in_m()}

[focuser]
best_position = {best_position}
um_per_step = {float(self["sky_um_per_step"])}

[psf]
model = "{self["sky_psf"]}"
"""
            + mount
        )
        self._mirage_key = key
        self._mirage_text = text
        self._mirage_sim = None  # the config moved, so the simulator must too
        self.log.debug(f"mirage config synthesized: {optics} f={focal_length}mm")
        return text

    def _simulator(self):
        """The mirage Simulator, or None with a named reason.

        Cached because building one opens the catalogue; rebuilt whenever
        `_mirage_config` decides the observatory changed underneath it.
        """
        text = self._mirage_config()
        if self._mirage_sim is not None:
            return self._mirage_sim
        try:
            import mirage
        except ImportError as e:
            self._sky_fallback_reason = (
                f"sky is set to mirage and mirage is not installed ({e}). It is in "
                f"chimera's dev dependency group -- `uv sync` -- because it builds "
                f"from Rust. Falling back to the DSS path"
            )
            self.log.warning(self._sky_fallback_reason)
            return None
        try:
            self._mirage_sim = mirage.Simulator.from_toml(
                text, catalog=self["sky_catalog"] or None
            )
        except Exception as e:
            self._sky_fallback_reason = (
                f"mirage would not open a star catalogue ({e}). It looks at the "
                f"sky_catalog config, then $GBX_CATALOG, then outward from the "
                f"running binary -- and a venv install is nowhere near a sibling "
                f"gbx checkout, so set sky_catalog. Falling back to the DSS path"
            )
            self.log.warning(self._sky_fallback_reason)
            return None
        return self._mirage_sim

    def _sky_mirage(self, telescope, image_request, binning_factor):
        """Render this exposure through mirage. None means "could not"."""
        sim = self._simulator()
        if sim is None:
            return None
        state = self._sky_state(telescope, image_request, binning_factor)
        # Shutter open, which is what `_expose` stamped and what `_save_image`
        # will write as DATE-OBS. mirage seeds its autonomous physics -- mount
        # error, seeing, ambient -- from this timestamp, so passing anything
        # else would put the frame's periodic error at a different phase from
        # the header that describes it.
        when = self.__last_frame_start or self._observatory_clock()[0]
        try:
            pixels, _header = sim.expose(
                ra=state["ra"],
                dec=state["dec"],
                exptime=state["exptime"],
                time=when.strftime("%Y-%m-%dT%H:%M:%SZ"),
                filter=state.get("filter", "V"),
                binning=state["binning"],
                temp_c=state.get("temp_c"),
                focus=state.get("focus"),
                guide_ra=state.get("guide_ra", 0.0),
                guide_dec=state.get("guide_dec", 0.0),
                ambient_c=state.get("ambient_c"),
                seeing=state.get("seeing"),
                rotator_pa=state.get("rotator_pa", 0.0),
                seed=state.get("seed", 0),
                side=state.get("side", "normal"),
            )
        except Exception as e:
            self._sky_fallback_reason = f"mirage could not render this exposure: {e}"
            self.log.warning(self._sky_fallback_reason)
            return None
        self.log.debug(
            f"mirage rendered {pixels.shape} at {state['ra']:.4f} {state['dec']:+.4f} "
            f"focus={state.get('focus')} filter={state.get('filter', 'V')} "
            f"pa={state.get('rotator_pa', 0.0)}"
        )
        # Returned as mirage made it: uint16, the same ADU array a real camera
        # would hand over. This used to cast to float32, which cost BITPIX, file
        # size, and -- because astropy quantizes floating-point input -- made
        # RICE compression lossy on a frame that had been exact integers.
        return pixels

    def _calibration_mirage(self, kind, image_request, binning_factor):
        """Render a bias, dark or flat through mirage. None means "could not".

        **Not gated on `sky`.** That option picks where the *sky* comes from,
        and none of these frames has any sky in them -- a dark is dark current,
        a bias is the read chain. What gates them is whether mirage is there at
        all, which is also why `make_dark`/`make_flat` stay as the fallback.

        No telescope and no dome either: a calibration frame has no pointing,
        so it can be taken by a camera sitting alone on a bench.
        """
        sim = self._simulator()
        if sim is None:
            return None
        state = self._detector_state(image_request, binning_factor)
        common = {
            "binning": state["binning"],
            "temp_c": state["temp_c"],
            "seed": state["seed"],
        }
        try:
            if kind == "BIAS":
                # No exptime: a bias is a zero-length exposure by definition.
                pixels, _header = sim.bias(**common)
            elif kind == "DARK":
                pixels, _header = sim.dark(state["exptime"], **common)
            else:
                pixels, _header = sim.flat(exptime=state["exptime"], **common)
        except Exception as e:
            self._sky_fallback_reason = f"mirage could not render a {kind.lower()}: {e}"
            self.log.warning(self._sky_fallback_reason)
            return None
        self.log.debug(f"mirage rendered a {kind.lower()} {pixels.shape}")
        return pixels

    def _readout(self, image_request):
        pix = None
        rendered_rotated = False
        telescope = None
        dome = None

        (mode, binning, top, left, width, height) = self._get_readout_mode_info(
            image_request["binning"], image_request["window"]
        )
        self.readout_begin(image_request)

        telescope = self.get_proxy("/Telescope/0")
        if not telescope.ping():
            telescope = None

        dome = self.get_proxy("/Dome/0")
        if not dome.ping():
            dome = None

        if self["rotator"]:
            rotator: Rotator = self.get_proxy(self["rotator"])
            if not rotator.ping():
                rotator = None
        else:
            rotator = None

        if not telescope:
            self.log.debug("FakeCamera couldn't find telescope.")
        if not dome:
            self.log.debug("FakeCamera couldn't find dome.")
        if not rotator:
            self.log.debug("FakeCamera couldn't find rotator.")

        ccd_width, ccd_height = self.get_physical_size()

        frame_type = image_request["type"].upper()

        if frame_type in ("DARK", "FLAT", "BIAS"):
            # **Calibration frames go through mirage too.** They are the same
            # detector as the sky frames -- same dark current, same read noise,
            # same temperature -- so rendering them from a different model would
            # make a dark that does not subtract off the frame it belongs to.
            self.log.info(f"making {frame_type.lower()}")
            pix = self._calibration_mirage(
                frame_type, image_request, self._binning_factors[binning]
            )
            # Rendered flat, and a calibration frame has no sky to rotate into
            # place -- resampling a bias would only smear its noise and zero the
            # corners.
            rendered_rotated = pix is not None

            if pix is None:
                # No mirage. The old synthetic frames, which are at least the
                # right shape and have noise in them.
                if frame_type == "DARK":
                    pix = self.make_dark(
                        (ccd_height, ccd_width), np.float32, image_request["exptime"]
                    )
                elif frame_type == "FLAT":
                    # No `/ 1000` any more: it turned a ~1000 ADU frame into
                    # ~1.0, which as integer ADU is a field of literal 1s.
                    pix = self.make_flat((ccd_height, ccd_width), np.float32)
                else:
                    pix = self.make_dark((ccd_height, ccd_width), np.float32, 0)
        else:
            # **The sky.** mirage needs a pointing, not a dome -- those two were
            # conflated here for years, which is most of why the DSS path below
            # was nearly unreachable. A dome, when there IS one, still decides
            # whether light gets in; without one, an open sky is the honest
            # reading of a rig that has no dome to close.
            if self._sky_source() == "mirage" and telescope is not None:
                if dome is None or dome.is_slit_open():
                    pix = self._sky_mirage(
                        telescope, image_request, self._binning_factors[binning]
                    )
                    # Rendered at the rotator's angle, so the resample below
                    # would apply it twice -- and it is the resample this path
                    # exists to avoid.
                    rendered_rotated = pix is not None
                else:
                    self.log.debug("Dome slit is shut; no sky for this exposure")

            if pix is None and self._dss_allowed() and telescope and dome:
                self.log.debug("Dome open? " + str(dome.is_slit_open()))

                if dome.is_slit_open() and self["use_dss"]:
                    dome_az = dome.get_az()
                    tel_az = telescope.get_az()

                    tel_position = Position.from_ra_dec(
                        *telescope.get_position_ra_dec(), epoch=Epoch.NOW
                    )
                    tel_position = tel_position.to_epoch(Epoch.J2000)

                    self.log.debug(
                        "Dome AZ: " + str(dome_az) + "  Tel AZ: " + str(tel_az)
                    )
                    if abs(dome_az - tel_az) <= 3:
                        self.log.debug("Dome & Slit aligned -- getting DSS")
                        url = "http://stdatu.stsci.edu/cgi-bin/dss_search?"
                        ra, dec = telescope.get_position_ra_dec()
                        query_args = {
                            "r": ra * 15,  # convert RA from hours to degrees
                            "d": dec,
                            "f": "fits",
                            "e": "j2000",
                            "c": "gz",
                            "fov": "NONE",
                        }

                        # use POSS2-Red surbey ( -90 < d < -20 ) if below -25 deg declination, else use POSS1-Red (-30 < d < +90)
                        # http://www-gsss.stsci.edu/SkySurveys/Surveys.htm
                        if tel_position.dec.deg < -25:
                            query_args["v"] = "poss2ukstu_red"
                            query_args["h"] = (
                                ccd_height / 59.5
                            )  # ~1"/pix (~60 pix/arcmin) is the plate scale of DSS POSS2-Red
                            query_args["w"] = ccd_width / 59.5
                        else:
                            query_args["v"] = "poss1_red"
                            query_args["h"] = (
                                ccd_height / 35.3
                            )  # 1.7"/pix (35.3 pix/arcmin) is the plate scale of DSS POSS1-Red
                            query_args["w"] = ccd_width / 35.3

                        url += urllib.parse.urlencode(query_args)

                        self.log.debug("Attempting URL: " + url)
                        try:
                            t0 = time.time()
                            dssfile = urllib.request.urlretrieve(url)[0]
                            self.log.debug("download took: %.3f s" % (time.time() - t0))
                            fitsfile = dssfile + ".fits.gz"
                            shutil.copy(dssfile, fitsfile)
                            hdulist = fits.open(fitsfile)
                            pix = hdulist[0].data
                            hdulist.close()
                            os.remove(fitsfile)
                        except Exception as e:
                            self.log.warning(
                                "General error getting DSS image: " + str(e)
                            )

                    # dome not aligned, take a 'dome flat'
                    else:
                        self.log.debug("Dome not aligned... making flat image...")
                        try:
                            pix = self.make_flat((ccd_height, ccd_width), np.float32)
                        except Exception as e:
                            self.log.warning("Error generating flat: " + str(e))

        # without telescope/dome, or if dome/telescope aren't aligned, or the dome is closed
        # or we otherwise failed, just make a flat pattern with dark noise
        if pix is None:
            try:
                self.log.info(
                    "Making flat image: " + str(ccd_height) + "x" + str(ccd_width)
                )
                pix = self.make_flat((ccd_height, ccd_width), np.float32)
            except Exception as e:
                self.log.warning("Make flat error: " + str(e))

        # Last resort if nothing else could make a picture
        if pix is None:
            pix = np.zeros((ccd_height, ccd_width), dtype=np.int32)

        # Rotate image. Position Angle (PA) is Counter-Clockwise.
        if rotator and not rendered_rotated:
            angle = rotator.get_position()
            self.log.debug(f"Rotating image by {angle} degrees")
            pix = self._rotate(pix, angle)

        # **This camera is 16 bits, and it is the camera that says so.** BITPIX
        # is not the requester's to choose -- see `ImageRequest` -- so the driver
        # settles it here, once, for every path above: mirage's uint16, the
        # float synthetic frames, whatever dtype a DSS cutout arrived in, and
        # the int32 last resort. One place, because `make_dark`/`make_flat`
        # cannot be handed a uint16 buffer to fill (in-place `+=` of float noise
        # will not cast) and so must keep computing in float regardless.
        #
        # Clip rather than cast: a stray negative or an above-full-well value is
        # a pixel at the end of its range, and wrapping would put it at the
        # other end. Same reasoning as `controllers/chz1streamer/core.py`.
        pix = np.clip(np.rint(pix), 0, 65535).astype(np.uint16)

        image = self._save_image(
            image_request,
            pix,
            {
                "frame_start_time": self.__last_frame_start,
                "frame_temperature": self.get_temperature(),
                "binning_factor": self._binning_factors[binning],
            },
        )

        # [ABORT POINT]
        if self.abort.is_set():
            self.readout_complete(None, CameraStatus.ABORTED)
            return None

        time.sleep(0.1 / self._observatory_clock()[1])  # simulate readout time
        self.readout_complete(image.url(), CameraStatus.OK)
        return image

    @lock
    def start_cooling(self, setpoint):
        self.__cooling = True
        self.__setpoint = setpoint
        return True

    @lock
    def stop_cooling(self):
        self.__cooling = False
        return True

    def is_cooling(self):
        return self.__cooling

    @lock
    def get_temperature(self):
        return self.__temperature + random.random()

    def get_set_point(self):
        return self.__setpoint

    @lock
    def start_fan(self, rate=None):
        self.__is_fanning = True

    @lock
    def stop_fan(self):
        self.__is_fanning = False

    def is_fanning(self):
        return self.__is_fanning

    def get_binnings(self):
        return self._binnings

    def get_adcs(self):
        return self._adcs

    def get_physical_size(self):
        return (self["ccd_width"], self["ccd_height"])

    def get_pixel_size(self):
        return (9, 9)

    def get_overscan_size(self):
        return (0, 0)

    def get_readout_modes(self):
        return self._readout_modes

    def supports(self, feature=None):
        return self._supports.get(feature, False)
