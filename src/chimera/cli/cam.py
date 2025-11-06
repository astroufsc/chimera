#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import copy
import os
import sys
import time

from chimera.core.exceptions import print_exception
from chimera.core.version import chimera_version
from chimera.interfaces.camera import CameraFeature, CameraStatus
from chimera.interfaces.filterwheel import InvalidFilterPositionException
from chimera.util.ds9 import DS9
from chimera.util.image import Image

from .cli import ChimeraCLI, ParameterType, action

current_frame = 0
current_frame_expose_start = 0
current_frame_readout_start = 0


def get_compressed_name(filename, compression):
    if compression.lower() == "no":
        return filename
    elif compression.lower() == "bz2":
        return filename + ".bz2"
    elif compression.lower() == "gzip":
        return filename + ".gz"
    elif compression.lower() == "zip":
        return filename + ".zip"
    elif compression.lower() == "fits_rice":
        return os.path.splitext(filename)[0] + ".fz"


class ChimeraCam(ChimeraCLI):
    def __init__(self):
        ChimeraCLI.__init__(self, "chimera-cam", "Camera controller", chimera_version)

        self.add_help_group("CAM", "Camera and Filter Wheel configuration")
        self.add_instrument(
            name="camera",
            cls="Camera",
            help="Camera instrument to be used. If blank, try to guess from chimera.config",
            help_group="CAM",
            required=True,
        )

        self.add_instrument(
            name="wheel",
            cls="FilterWheel",
            help="Filter Wheel instrument to be used. If blank, try to guess from chimera.config",
            help_group="CAM",
        )

        self.add_instrument(
            name="dome",
            cls="Dome",
            help="Dome instrument to be used. If blank, try to guess from chimera.config",
            help_group="CAM",
        )

        self.add_help_group("EXPOSE", "Exposure control")
        self.add_parameters(
            dict(
                name="frames",
                short="n",
                type="int",
                default=1,
                help_group="EXPOSE",
                help="Number of frames",
            ),
            dict(
                name="exptime",
                short="t",
                type="string",
                default=1,
                help_group="EXPOSE",
                help="Integration time in seconds for each frame",
            ),
            dict(
                name="interval",
                short="i",
                type="float",
                default=0.0,
                help_group="EXPOSE",
                help="Number of seconds to wait between each frame",
            ),
            dict(
                name="output",
                short="o",
                type="string",
                help_group="EXPOSE",
                help="Base filename including full path if needed.",
                default="$DATE-$TIME.fits",
            ),
            dict(
                name="filter",
                long="filters",
                short="f",
                type="string",
                help_group="EXPOSE",
                help="Filter(s) to be used. "
                "Use --list-filters to get a list of available filters. "
                "You can pass a comma-separated list of filter to get multiple exposure (in the same order as the filter list).",
            ),
            dict(
                name="shutter",
                type=ParameterType.CHOICE,
                help_group="EXPOSE",
                choices=[
                    "open",
                    "OPEN",
                    "close",
                    "CLOSE",
                    "leave",
                    "LEAVE",
                    "default",
                    "DEFAULT",
                ],
                default="default",
                help="What to do with the shutter: open, close, leave (case insensitive) or "
                "default to adjust according to image type (see --object and family",
            ),
            dict(
                name="binning",
                help="Apply the selected binning to all frames",
                help_group="EXPOSE",
            ),
            dict(
                name="subframe",
                help="Readout only the selected subframe portion. The notation follows IRAF conventions."
                " x1:x2,y1:y2 to specify the corners of the desired subframe",
                help_group="EXPOSE",
            ),
            dict(
                name="compress",
                help="Compress the output file using FORMAT. Use --compress=no to disable it.",
                help_group="EXPOSE",
                type=ParameterType.CHOICE,
                choices=[
                    "FITS_RICE",
                    "BZ2",
                    "ZIP",
                    "GZIP",
                    "NO",
                    "fits_rice",
                    "bz2",
                    "zip",
                    "gzip",
                    "no",
                ],
                default="no",
            ),
            dict(
                name="ignore_dome",
                long="ignore-dome",
                type=ParameterType.BOOLEAN,
                default=False,
                help_group="EXPOSE",
                help="Ignore if the dome is slewing, take an image anyway.",
            ),
        )

        self.add_help_group("DISPLAY", "Display configuration")
        self.add_parameters(
            dict(
                name="disable_display",
                long="disable-display",
                type=ParameterType.BOOLEAN,
                help_group="DISPLAY",
                help="Don't try to display image on DS9. default is display for exptime >= 5",
            ),
            dict(
                name="force_display",
                long="force-display",
                type=ParameterType.BOOLEAN,
                help_group="DISPLAY",
                help="Always display image on DS9 regardless of exptime.",
            ),
        )

        self.add_help_group("TEMP", "Temperature control")
        self.add_parameters(
            dict(
                name="wait",
                short="w",
                type=ParameterType.BOOLEAN,
                default=False,
                help_group="TEMP",
                help="Wait until the selected CCD setpoint is achived.",
            )
        )

        self.add_help_group("INFO", "Information")

        self.add_help_group("IMAGETYPE", "Image types")
        self.add_parameters(
            dict(
                name="is_bias",
                long="bias",
                type=ParameterType.CONSTANT,
                const="zero",
                help="Mark this frame as a BIAS frame.",
                help_group="IMAGETYPE",
            ),
            dict(
                name="is_dome_flat",
                long="flat",
                type=ParameterType.CONSTANT,
                const="flat",
                help="Mark this frame as a DOME FLAT frame.",
                help_group="IMAGETYPE",
            ),
            dict(
                name="is_sky_flat",
                long="sky-flat",
                type=ParameterType.CONSTANT,
                const="skyflat",
                help="Mark this frame as a SKY FLAT frame.",
                help_group="IMAGETYPE",
            ),
            dict(
                name="is_dark",
                long="dark",
                type=ParameterType.CONSTANT,
                const="dark",
                help="Mark this frame as a DARK frame.",
                help_group="IMAGETYPE",
            ),
            dict(
                name="is_object",
                long="object",
                type="string",
                default="object",
                help="Mark this frame as a OBJECT frame and add OBJECT keyword to the FITS file using OBJECTNAME.",
                help_group="IMAGETYPE",
                metavar="OBJECTNAME",
            ),
        )

    @action(
        short="F",
        long="--list-filters",
        help_group="INFO",
        help="Print available filter names.",
    )
    def filters(self, options):
        if not hasattr(self, "wheel"):
            self.exit("No Filter Wheel instrument configured.")
        if not self.wheel:
            self.exit(
                "No Filter Wheel found. Edit chimera.config or pass --wheel (see --help)"
            )

        self.out("Available filters:", end="")

        for i, f in enumerate(self.wheel.get_filters()):
            self.out(str(f), end="")

        self.out()
        self.exit()

    @action(
        name="setpoint",
        short="T",
        long="start-cooling",
        action_group="TEMP",
        type="float",
        help_group="TEMP",
        help="Start camera cooling, using the defined TEMP",
        metavar="TEMP",
    )
    def start_cooling(self, options):
        def eps_equal(a, b, eps=0.01):
            return abs(a - b) <= eps

        camera = self.camera

        if options.wait:
            timeout = 4 * 60  # FIXME: configurable?

        start = time.time()

        self.out(40 * "=")

        camera.start_cooling(options.setpoint)
        self.out("setting camera setpoint to %.3f." % options.setpoint)

        if options.wait:
            while not eps_equal(camera.get_temperature(), camera.get_set_point(), 0.2):
                self.out(
                    "\rwaiting setpoint temperature %.3f oC, current: %.3f oC"
                    % (camera.get_set_point(), camera.get_temperature()),
                    end="",
                )
                time.sleep(1)

                if time.time() > (start + timeout):
                    self.out("giving up after wait for %d seconds" % timeout)
                    break

            self.out("OK (took %.3fs)" % (time.time() - start))

        self.out(40 * "=")
        self.exit()

    @action(
        long="stop-cooling",
        action_group="TEMP",
        help_group="TEMP",
        help="Stop camera cooling",
    )
    def stop_cooling(self, options):
        camera = self.camera

        self.out(40 * "=")
        self.out("stopping camera cooling...", end="")
        camera.stop_cooling()
        self.out("OK")
        self.out(40 * "=")
        self.exit()

    @action(
        long="stop-fan",
        action_group="TEMP_FAN",
        help_group="TEMP",
        help="Stop the cooler fan.",
    )
    def stop_fan(self, options):
        camera = self.camera

        self.out(40 * "=")
        self.out("stopping cooler fan...", end="")
        camera.stop_fan()
        self.out("OK")
        self.out(40 * "=")
        self.exit()

    @action(
        long="start-fan",
        action_group="TEMP_FAN",
        help_group="TEMP",
        help="Start the cooler fan.",
    )
    def start_fan(self, options):
        camera = self.camera

        self.out(40 * "=")
        self.out("starting cooler fan...", end="")
        camera.start_fan()
        self.out("OK")
        self.out(40 * "=")
        self.exit()

    @action(help="Print camera information and exit", help_group="INFO")
    def info(self, options):
        camera = self.camera

        self.out("=" * 40)
        self.out("Camera: %s (%s)." % (camera.get_location(), camera["device"]))

        if camera.is_cooling() is True:
            self.out("Cooling enabled, Setpoint: %.1f oC" % camera.get_set_point())
        else:
            self.out("Cooling disabled.")

        self.out("Current CCD temperature:", "%.1f" % camera.get_temperature(), "oC")
        if camera.is_fanning():
            self.out("Cooler fan active.")
        else:
            self.out("Cooler fan inactive.")

        self.out("=" * 40)
        for feature in CameraFeature:
            self.out(str(feature), str(bool(camera.supports(feature))))

        self.out("=" * 40)
        ccds = camera.get_ccds()
        current_ccd = camera.get_current_ccd()
        self.out("Available CCDs: ", end="")
        for ccd in list(ccds.keys()):
            if ccd == current_ccd:
                self.out("*%s* " % str(ccds[ccd]), end="")
            else:
                self.out("%s " % str(ccds[ccd]), end="")
        self.out()

        self.out("=" * 40)
        self.out("ADCs: ", end="")
        adcs = camera.get_adcs()
        for adc in list(adcs.keys()):
            self.out("%s " % adc, end="")
        self.out()

        pix_w, pix_h = camera.get_pixel_size()
        pix_w_um, pix_h_um = camera.get_physical_size()
        overscan_w, overscan_h = camera.get_overscan_size()

        self.out("=" * 40)
        self.out(f"CCD size (pixel)       : {pix_w} x {pix_h}")
        self.out(f"Pixel size (micrometer): {pix_w_um:.2f} x {pix_h_um:.2f}")
        self.out(f"Overscan size (pixel)  : {overscan_w} x {overscan_h}")

        self.out("=" * 40)
        self.out("Available binnings: ", end="")
        sorted_bins = list(camera.get_binnings().keys())
        sorted_bins.sort()

        for bin in sorted_bins:
            self.out("%s " % bin, end="")
        self.out()

        self.out("=" * 40)

        self.exit()

    def _get_image_type(self, options):
        special_types = (
            options.is_bias,
            options.is_dome_flat,
            options.is_sky_flat,
            options.is_dark,
        )
        for t in special_types:
            if t:
                return t
        return "object"

    def __abort__(self):
        self.out("\naborting... ", endl="")

        # copy self.camera Proxy because we are running from a different
        # thread
        if hasattr(self, "camera"):
            cam = copy.copy(self.camera)
            cam.abort_exposure()

    @action(
        # default=True,
        help_group="EXPOSE",
        help="Take an exposure with selected parameters",
    )
    def expose(self, options):
        camera = self.camera

        # first check binning
        binnings = camera.get_binnings()

        if options.binning:
            if options.binning not in list(binnings.keys()):
                self.exit(
                    "Invalid binning mode. See --info for available binning modes"
                )

        imagetype = self._get_image_type(options)
        if imagetype == "object":
            object_name = options.is_object
        else:
            object_name = None

        if imagetype == "zero":
            if options.exptime > 0:
                self.out("=" * 40)
                self.out(
                    "WARNING: Bias image requested, forcing exptime=0 and shutter closed"
                )
            options.exptime = 0.0

        # adjust shutter according to Image type if shutter set to default.
        if "default" in options.shutter.lower():
            if imagetype == "zero":
                options.shutter = "CLOSE"

            elif imagetype == "dark":
                options.shutter = "CLOSE"

            elif "flat" in imagetype or imagetype == "object":
                options.shutter = "OPEN"

            else:
                options.shutter = "OPEN"

        else:
            # make sure we use ALL CAPS here, Enums doesn't like lower case
            # names.
            options.shutter = options.shutter.upper()

        # filter/exptime list support
        filter_list = []

        if options.filter is not None:
            if "," in options.filter:
                for f in options.filter.split(","):
                    filter_list.append(f.strip())
            else:
                filter_list.append(options.filter)

            # validate filters
            for filter_name in filter_list:
                if self.wheel and filter_name not in self.wheel.get_filters():
                    self.err("Invalid filter '%s'" % filter_name)
                    self.exit()

            self.out("Filters: %s" % " ".join(filter_list))

        exp_times = []
        if isinstance(options.exptime, str) and "," in options.exptime:
            for exp in options.exptime.split(","):
                exp_times.append(float(exp))
        else:
            exp_times.append(float(options.exptime))

        # match exp_times and filter_list (if last given)
        if filter_list:
            # use last given exptime if there are more filter than exptimes (if
            # less, we just ignore).
            if len(exp_times) < len(filter_list):
                exps = [exp_times[-1] for x in range(len(filter_list) - len(exp_times))]
                exp_times.extend(exps)

        compress_format = options.compress

        # DS9
        ds9 = None
        if (
            not self.options.disable_display and exp_times[0] >= 5
        ) or options.force_display:
            try:
                ds9 = DS9(open=True)
            except OSError:
                self.err("Problems starting DS9. DIsplay disabled.")

        def expose_begin(request):
            global current_frame, current_frame_expose_start
            current_frame_expose_start = time.time()
            current_frame += 1
            self.out(40 * "=")
            self.out(
                "[%03d/%03d] [%s]"
                % (current_frame, options.frames, time.strftime("%c"))
            )
            self.out("exposing (%.3fs) ..." % request["exptime"], end="")

        def expose_complete(request, status):
            global current_frame_expose_start
            if status == CameraStatus.OK:
                self.out(
                    "OK (took %.3f s)" % (time.time() - current_frame_expose_start)
                )

        def readout_begin(request):
            global current_frame_readout_start
            current_frame_readout_start = time.time()
            self.out("reading out and saving ...", end="")

        def readout_complete(image_url, status):
            global current_frame, current_frame_expose_start, current_frame_readout_start

            image = Image.from_url(image_url)

            if status == CameraStatus.OK:
                self.out(
                    "OK (took %.3f s)" % (time.time() - current_frame_expose_start)
                )

                self.out(
                    " (%s) " % get_compressed_name(image.filename, compress_format),
                    end="",
                )
                self.out(
                    "OK (took %.3f s)" % (time.time() - current_frame_readout_start)
                )
                self.out(
                    "[%03d/%03d] took %.3fs"
                    % (
                        current_frame,
                        options.frames,
                        time.time() - current_frame_expose_start,
                    )
                )

                if ds9:
                    ds9.set("scale mode 99.5")
                    ds9.display_image(image)

        camera.expose_begin += expose_begin
        camera.expose_complete += expose_complete
        camera.readout_begin += readout_begin
        camera.readout_complete += readout_complete

        # do we have a Dome?
        dome = self.dome if hasattr(self, "dome") else None

        if dome:

            def sync_begin():
                self.out("=" * 40)
                self.out("synchronizing dome slit ...", end="")

            def sync_complete():
                self.out("OK")

            dome.sync_begin += sync_begin
            dome.sync_complete += sync_complete

        self.out(40 * "=")
        self.out("Taking %d %s frame[s]" % (options.frames, imagetype.upper()))
        self.out("Shutter: %s" % options.shutter)
        self.out("Interval between frames: %.3fs" % options.interval)
        if camera.is_cooling():
            self.out("Cooling enabled, setpoint: %.3f oC" % camera.get_set_point())
        else:
            self.out("Cooling disabled.")

        self.out("Current CCD temperature: %.3f oC" % camera.get_temperature())

        if options.binning:
            self.out("Binning: %s" % options.binning)
        else:
            self.out("No binning")

        if options.subframe:
            self.out("Subframe: %s" % options.subframe)
        else:
            self.out("Full Frame")

        def change_filter(f):
            if options.filter is not None and self.wheel:
                self.out(40 * "=")
                try:
                    self.out("Changing to filter %s... " % f, end="")
                    self.wheel.set_filter(f)
                    self.out("OK")
                except InvalidFilterPositionException as e:
                    self.err("ERROR. Couldn't move filter wheel to %s. (%s)" % (f, e))
                    self.exit()

        # finally, expose
        start = time.time()

        try:
            try:
                if filter_list:
                    for f in range(len(filter_list)):
                        change_filter(filter_list[f])

                        if (options.interval > 0) and (1 <= f < (len(filter_list))):
                            self.out("=" * 40)
                            self.out(
                                "waiting %.2f s before next frame..." % options.interval
                            )
                            time.sleep(options.interval)

                        camera.expose(
                            exptime=exp_times[f],
                            frames=options.frames,
                            interval=options.interval,
                            filename=options.output,
                            type=imagetype,
                            binning=options.binning or None,
                            window=options.subframe or None,
                            shutter=options.shutter,
                            compress_format=compress_format,
                            wait_dome=not options.ignore_dome,
                            object_name=object_name,
                        )

                else:
                    camera.expose(
                        exptime=exp_times[0],
                        frames=options.frames,
                        interval=options.interval,
                        filename=options.output,
                        type=imagetype,
                        binning=options.binning or None,
                        window=options.subframe or None,
                        shutter=options.shutter,
                        compress_format=compress_format,
                        wait_dome=not options.ignore_dome,
                        object_name=object_name,
                    )

            except OSError as e:
                self.err("Error trying to take exposures (%s)" % str(e))
            except Exception as e:
                self.err("Error trying to take exposures. (%s)" % print_exception(e))
        finally:
            self.out(40 * "=")
            self.out("Total time: %.3fs" % (time.time() - start))
            self.out(40 * "=")
            self.out("%s" % time.strftime("%c"))
            self.out(40 * "=")

            # fixme: Should not be necessary. Bus should handle this.
            camera.expose_begin -= expose_begin
            camera.expose_complete -= expose_complete
            camera.readout_begin -= readout_begin
            camera.readout_complete -= readout_complete
            if dome:
                dome.sync_begin -= sync_begin
                dome.sync_complete -= sync_complete
            # fixme: end
            


def main():
    cli = ChimeraCam()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
