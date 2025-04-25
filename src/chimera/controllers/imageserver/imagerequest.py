import logging

from chimera.interfaces.camera import Shutter, Bitpix
from chimera.core.exceptions import ChimeraValueError, ObjectNotFoundException

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

    def begin_exposure(self, manager):

        self._fetch_pre_headers(manager)

        if self["wait_dome"]:
            try:
                dome = manager.get_proxy(manager.get_resources_by_class("Dome")[0])
                dome.sync_with_tel()
                log.debug("Dome slit position synchronized with telescope position.")
            except (ObjectNotFoundException, IndexError):
                log.info("No dome present, taking exposure without dome sync.")

    def end_exposure(self, manager):
        self._fetch_post_headers(manager)

    def _fetch_pre_headers(self, manager):
        auto = []
        if self.auto_collect_metadata:
            for cls in (
                "Site",
                "Camera",
                "Dome",
                "FilterWheel",
                "Focuser",
                "Telescope",
                "WeatherStation",
                "SeeingMonitor",
            ):
                locations = manager.get_resources_by_class(cls)
                if len(locations) == 1:
                    auto.append(str(locations[0]))
                elif len(locations) == 0:
                    log.warning(f"No {cls} available, header would be incomplete.")
                else:
                    log.warning(
                        f"More than one {cls} available, header may be incorrect. Using the first {cls}."
                    )
                    auto.append(str(locations[0]))

            self._get_headers(manager, auto + self.metadata_pre)

    def _fetch_post_headers(self, manager):
        self._get_headers(manager, self.metadata_post)

    def _get_headers(self, manager, locations):

        for location in locations:

            if location not in self._proxies:
                try:
                    self._proxies[location] = manager.get_proxy(location)
                except Exception:
                    log.exception(f"Unable to get metadata from {location}")

            self.headers += self._proxies[location].get_metadata(self)
