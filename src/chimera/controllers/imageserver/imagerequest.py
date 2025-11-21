import logging

from chimera.core.exceptions import ChimeraValueError
from chimera.interfaces.camera import Bitpix, Shutter

log = logging.getLogger(__name__)


class ImageRequest(dict):
    valid_keys = [
        "exptime",
        "frames",
        "interval",
        "shutter",
        "binning",
        "window",
        "bitpix",
        "filename",
        "compress_format",
        "type",
        "wait_dome",
        "object_name",
    ]

    def __init__(self, **kwargs):
        defaults = {
            "exptime": 1.0,
            "frames": 1,
            "interval": 0.0,
            "shutter": Shutter.OPEN,
            "binning": "1x1",
            "window": None,
            "bitpix": Bitpix.uint16,
            "filename": "$DATE-$TIME",
            "compress_format": "NO",
            "type": "object",
            "wait_dome": True,
            "object_name": "",
        }

        # Automatically call get_metadata on all instruments + site as long
        # as only one instance of each is listed by the manager.
        self.auto_collect_metadata = True

        # URLs of proxies from which to get metadata before taking each image
        self.metadata_pre = []

        # URLs of proxies from which to get metadata after taking each image
        self.metadata_post = []

        # Headers accumulated during processing of each frame
        # (=headers+metadata_pre+metadata_post)
        self.headers = []

        self._proxies = {}

        self.update(defaults)

        # validate keywords passed
        not_valid = [k for k in list(kwargs.keys()) if k not in list(defaults.keys())]

        if any(not_valid):
            if len(not_valid) > 1:
                msg = "Invalid keywords: "
                for k in not_valid:
                    msg += f"'{str(k)}', "
                msg = msg[:-2]

            else:
                msg = f"Invalid keyword '{str(not_valid[0])}'"

            raise TypeError(msg)

        self.update(kwargs)

        # do some checkings
        if self["exptime"] < 0.0:
            raise ChimeraValueError("Invalid exposure length (<0 seconds).")

        # FIXME: magic number here! But we shouldn't allow arbitrary maximum
        # for safety reasons.
        if self["exptime"] > 12 * 60 * 60:
            raise ChimeraValueError("Invalid exposure. Must be lower them 12 hours.")

        if self["frames"] < 1:
            raise ChimeraValueError("Invalid number of frames (<1 frame).")

        if self["interval"] < 0.0:
            raise ChimeraValueError("Invalid interval between exposures (<0 seconds)")

        if str(self["shutter"]) not in Shutter:
            raise ChimeraValueError("Invalid shutter value: " + str(self["shutter"]))
        else:
            self["shutter"] = Shutter[self["shutter"]]

        if self["object_name"]:
            self.headers.append(
                ("OBJECT", str(self["object_name"]), "name of observed object")
            )

    def __setitem__(self, key, value):
        if key not in ImageRequest.valid_keys:
            raise KeyError(f"{key} is not a valid key for ImageRequest")

        self.update({key: value})

    def __str__(self):
        return f"exptime: {self['exptime']:.6f}, frames: {self['frames']}, shutter: {self['shutter']}, type: {self['type']}"

    def begin_exposure(self, chimera_obj):
        self._fetch_pre_headers(chimera_obj)

        if self["wait_dome"]:
            dome = chimera_obj.get_proxy("/Dome/0")
            if not dome.ping():
                log.info("No dome present, taking exposure without dome sync.")
                return
            dome.sync_with_tel()
            if dome.is_sync_with_tel():
                log.debug("Dome slit position synchronized with telescope position.")
            else:
                log.info(
                    "Dome slit position could not be synchronized with telescope position."
                )

    def end_exposure(self, chimera_obj):
        self._fetch_post_headers(chimera_obj)

    def _fetch_pre_headers(self, chimera_obj):
        auto = []
        if self.auto_collect_metadata:
            auto += [
                f"/{cls}/0"
                for cls in (
                    "Site",
                    "Camera",
                    "Dome",
                    "FilterWheel",
                    "Focuser",
                    "Telescope",
                    "WeatherStation",
                )
            ]

            self._get_headers(chimera_obj, auto + self.metadata_pre)

    def _fetch_post_headers(self, chimera_obj):
        self._get_headers(chimera_obj, self.metadata_post)

    def _get_headers(self, chimera_obj, locations):
        for location in locations:
            if location not in self._proxies:
                self._proxies[location] = chimera_obj.get_proxy(location)
            try:
                self.headers += self._proxies[location].get_metadata(self)
            except Exception:
                log.warning(f"Unable to get metadata from {location}")
