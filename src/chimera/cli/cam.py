#!/usr/bin/env python
# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import copy
import os
import sys
import time

from chimera.core.exceptions import ObjectNotFoundException, printException
from chimera.core.version import _chimera_version_
from chimera.interfaces.camera import CameraFeature, CameraStatus
from chimera.interfaces.filterwheel import InvalidFilterPositionException
from chimera.util.ds9 import DS9

from .cli import ChimeraCLI, ParameterType, action

currentFrame = 0
currentFrameExposeStart = 0
currentFrameReadoutStart = 0


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
        ChimeraCLI.__init__(self, "chimera-cam", "Camera controller", _chimera_version_)

        self.addHelpGroup("CAM", "Camera and Filter Wheel configuration")
        self.addInstrument(
            name="camera",
            cls="Camera",
            help="Camera instrument to be used. If blank, try to guess from chimera.config",
            helpGroup="CAM",
            required=True,
        )

        self.addInstrument(
            name="wheel",
            cls="FilterWheel",
            help="Filter Wheel instrument to be used. If blank, try to guess from chimera.config",
            helpGroup="CAM",
        )

        self.addHelpGroup("EXPOSE", "Exposure control")
        self.addParameters(
            dict(
                name="frames",
                short="n",
                type="int",
                default=1,
                helpGroup="EXPOSE",
                help="Number of frames",
            ),
            dict(
                name="exptime",
                short="t",
                type="string",
                default=1,
                helpGroup="EXPOSE",
                help="Integration time in seconds for each frame",
            ),
            dict(
                name="interval",
                short="i",
                type="float",
                default=0.0,
                helpGroup="EXPOSE",
                help="Number of seconds to wait between each frame",
            ),
            dict(
                name="output",
                short="o",
                type="string",
                helpGroup="EXPOSE",
                help="Base filename including full path if needed.",
                default="$DATE-$TIME.fits",
            ),
            dict(
                name="filter",
                long="filters",
                short="f",
                type="string",
                helpGroup="EXPOSE",
                help="Filter(s) to be used. "
                "Use --list-filters to get a list of available filters. "
                "You can pass a comma-separated list of filter to get multiple exposure (in the same order as the filter list).",
            ),
            dict(
                name="shutter",
                type=ParameterType.CHOICE,
                helpGroup="EXPOSE",
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
                helpGroup="EXPOSE",
            ),
            dict(
                name="subframe",
                help="Readout only the selected subframe portion. The notation follows IRAF conventions."
                " x1:x2,y1:y2 to specify the corners of the desired subframe",
                helpGroup="EXPOSE",
            ),
            dict(
                name="compress",
                help="Compress the output file using FORMAT. Use --compress=no to disable it.",
                helpGroup="EXPOSE",
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
                helpGroup="EXPOSE",
                help="Ignore if the dome is slewing, take an image anyway.",
            ),
        )

        self.addHelpGroup("DISPLAY", "Display configuration")
        self.addParameters(
            dict(
                name="disable_display",
                long="disable-display",
                type=ParameterType.BOOLEAN,
                helpGroup="DISPLAY",
                help="Don't try to display image on DS9. default is display for exptime >= 5",
            ),
            dict(
                name="force_display",
                long="force-display",
                type=ParameterType.BOOLEAN,
                helpGroup="DISPLAY",
                help="Always display image on DS9 regardless of exptime.",
            ),
        )

        self.addHelpGroup("TEMP", "Temperature control")
        self.addParameters(
            dict(
                name="wait",
                short="w",
                type=ParameterType.BOOLEAN,
                default=False,
                helpGroup="TEMP",
                help="Wait until the selected CCD setpoint is achived.",
            )
        )

        self.addHelpGroup("INFO", "Information")

        self.addHelpGroup("IMAGETYPE", "Image types")
        self.addParameters(
            dict(
                name="isBias",
                long="bias",
                type=ParameterType.CONSTANT,
                const="zero",
                help="Mark this frame as a BIAS frame.",
                helpGroup="IMAGETYPE",
            ),
            dict(
                name="isDomeFlat",
                long="flat",
                type=ParameterType.CONSTANT,
                const="flat",
                help="Mark this frame as a DOME FLAT frame.",
                helpGroup="IMAGETYPE",
            ),
            dict(
                name="isSkyFlat",
                long="sky-flat",
                type=ParameterType.CONSTANT,
                const="skyflat",
                help="Mark this frame as a SKY FLAT frame.",
                helpGroup="IMAGETYPE",
            ),
            dict(
                name="isDark",
                long="dark",
                type=ParameterType.CONSTANT,
                const="dark",
                help="Mark this frame as a DARK frame.",
                helpGroup="IMAGETYPE",
            ),
            dict(
                name="isObject",
                long="object",
                type="string",
                default="object",
                help="Mark this frame as a OBJECT frame and add OBJECT keyword to the FITS file using OBJECTNAME.",
                helpGroup="IMAGETYPE",
                metavar="OBJECTNAME",
            ),
        )

    @action(
        short="F",
        long="--list-filters",
        helpGroup="INFO",
        help="Print available filter names.",
    )
    def filters(self, options):
        if not self.wheel:
            self.exit(
                "No Filter Wheel found. Edit chimera.config or pass --wheel (see --help)"
            )

        self.out("Available filters:", end="")

        for i, f in enumerate(self.wheel.getFilters()):
            self.out(str(f), end="")

        self.out()
        self.exit()

    @action(
        name="setpoint",
        short="T",
        long="start-cooling",
        actionGroup="TEMP",
        type="float",
        helpGroup="TEMP",
        help="Start camera cooling, using the defined TEMP",
        metavar="TEMP",
    )
    def startCooling(self, options):
        def eps_equal(a, b, eps=0.01):
            return abs(a - b) <= eps

        camera = self.camera

        if options.wait:
            timeout = 4 * 60  # FIXME: configurable?

        start = time.time()

        self.out(40 * "=")

        camera.startCooling(options.setpoint)
        self.out("setting camera setpoint to %.3f." % options.setpoint)

        if options.wait:
            while not eps_equal(camera.getTemperature(), camera.getSetPoint(), 0.2):
                self.out(
                    "\rwaiting setpoint temperature %.3f oC, current: %.3f oC"
                    % (camera.getSetPoint(), camera.getTemperature()),
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
        actionGroup="TEMP",
        helpGroup="TEMP",
        help="Stop camera cooling",
    )
    def stopCooling(self, options):
        camera = self.camera

        self.out(40 * "=")
        self.out("stopping camera cooling...", end="")
        camera.stopCooling()
        self.out("OK")
        self.out(40 * "=")
        self.exit()

    @action(
        long="stop-fan",
        actionGroup="TEMP_FAN",
        helpGroup="TEMP",
        help="Stop the cooler fan.",
    )
    def stopFan(self, options):
        camera = self.camera

        self.out(40 * "=")
        self.out("stopping cooler fan...", end="")
        camera.stopFan()
        self.out("OK")
        self.out(40 * "=")
        self.exit()

    @action(
        long="start-fan",
        actionGroup="TEMP_FAN",
        helpGroup="TEMP",
        help="Start the cooler fan.",
    )
    def startFan(self, options):
        camera = self.camera

        self.out(40 * "=")
        self.out("starting cooler fan...", end="")
        camera.startFan()
        self.out("OK")
        self.out(40 * "=")
        self.exit()

    @action(help="Print camera information and exit", helpGroup="INFO")
    def info(self, options):
        camera = self.camera

        self.out("=" * 40)
        self.out("Camera: %s (%s)." % (camera.getLocation(), camera["device"]))

        if camera.isCooling() is True:
            self.out("Cooling enabled, Setpoint: %.1f oC" % camera.getSetPoint())
        else:
            self.out("Cooling disabled.")

        self.out("Current CCD temperature:", "%.1f" % camera.getTemperature(), "oC")
        if camera.isFanning():
            self.out("Cooler fan active.")
        else:
            self.out("Cooler fan inactive.")

        self.out("=" * 40)
        for feature in CameraFeature:
            self.out(str(feature), str(bool(camera.supports(feature))))

        self.out("=" * 40)
        ccds = camera.getCCDs()
        currentCCD = camera.getCurrentCCD()
        self.out("Available CCDs: ", end="")
        for ccd in list(ccds.keys()):
            if ccd == currentCCD:
                self.out("*%s* " % str(ccds[ccd]), end="")
            else:
                self.out("%s " % str(ccds[ccd]), end="")
        self.out()

        self.out("=" * 40)
        self.out("ADCs: ", end="")
        adcs = camera.getADCs()
        for adc in list(adcs.keys()):
            self.out("%s " % adc, end="")
        self.out()

        self.out("=" * 40)
        self.out("CCD size (pixel)       : %d x %d" % camera.getPhysicalSize())
        self.out("Pixel size (micrometer): %.2f x %.2f" % camera.getPixelSize())
        self.out("Overscan size (pixel)  : %d x %d" % camera.getOverscanSize())

        self.out("=" * 40)
        self.out("Available binnings: ", end="")
        sortedBins = list(camera.getBinnings().keys())
        sortedBins.sort()

        for bin in sortedBins:
            self.out("%s " % bin, end="")
        self.out()

        self.out("=" * 40)

        self.exit()

    def _getImageType(self, options):
        special_types = (
            options.isBias,
            options.isDomeFlat,
            options.isSkyFlat,
            options.isDark,
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
            cam.abortExposure()

    @action(
        default=True,
        helpGroup="EXPOSE",
        help="Take an exposure with selected parameters",
    )
    def expose(self, options):
        camera = self.camera

        # first check binning
        binnings = camera.getBinnings()

        if options.binning:
            if options.binning not in list(binnings.keys()):
                self.exit(
                    "Invalid binning mode. See --info for available binning modes"
                )

        imagetype = self._getImageType(options)
        if imagetype == "object":
            object_name = options.isObject
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
        filterList = []

        if options.filter is not None:
            if "," in options.filter:
                for f in options.filter.split(","):
                    filterList.append(f.strip())
            else:
                filterList.append(options.filter)

            # validate filters
            for filter in filterList:
                if self.wheel and filter not in self.wheel.getFilters():
                    self.err("Invalid filter '%s'" % filter)
                    self.exit()

            self.out("Filters: %s" % " ".join(filterList))

        expTimes = []
        if isinstance(options.exptime, str) and "," in options.exptime:
            for exp in options.exptime.split(","):
                expTimes.append(float(exp))
        else:
            expTimes.append(float(options.exptime))

        # match expTimes and filterFist (if last given)
        if filterList:
            # use last given exptime if there are more filter than exptimes (if
            # less, we just ignore).
            if len(expTimes) < len(filterList):
                exps = [expTimes[-1] for x in range(len(filterList) - len(expTimes))]
                expTimes.extend(exps)

        compress_format = options.compress

        # DS9
        ds9 = None
        if (
            not self.options.disable_display and expTimes[0] >= 5
        ) or options.force_display:
            try:
                ds9 = DS9(open=True)
            except IOError:
                self.err("Problems starting DS9. DIsplay disabled.")

        def exposeBegin(request):
            global currentFrame, currentFrameExposeStart
            currentFrameExposeStart = time.time()
            currentFrame += 1
            self.out(40 * "=")
            self.out(
                "[%03d/%03d] [%s]" % (currentFrame, options.frames, time.strftime("%c"))
            )
            self.out("exposing (%.3fs) ..." % request["exptime"], end="")

        def exposeComplete(request, status):
            global currentFrameExposeStart
            if status == CameraStatus.OK:
                self.out("OK (took %.3f s)" % (time.time() - currentFrameExposeStart))

        def readoutBegin(request):
            global currentFrameReadoutStart
            currentFrameReadoutStart = time.time()
            self.out("reading out and saving ...", end="")

        def readoutComplete(image, status):
            global currentFrame, currentFrameExposeStart, currentFrameReadoutStart

            if status == CameraStatus.OK:
                self.out("OK (took %.3f s)" % (time.time() - currentFrameExposeStart))

                self.out(
                    " (%s) " % get_compressed_name(image.filename, compress_format),
                    end="",
                )
                self.out("OK (took %.3f s)" % (time.time() - currentFrameReadoutStart))
                self.out(
                    "[%03d/%03d] took %.3fs"
                    % (
                        currentFrame,
                        options.frames,
                        time.time() - currentFrameExposeStart,
                    )
                )

                if ds9:
                    ds9.set("scale mode 99.5")
                    ds9.displayImage(image)

        camera.exposeBegin += exposeBegin
        camera.exposeComplete += exposeComplete
        camera.readoutBegin += readoutBegin
        camera.readoutComplete += readoutComplete

        # do we have a Dome?
        dome = None
        remoteManager = camera.getManager()
        try:
            dome = remoteManager.getProxy(remoteManager.getResourcesByClass("Dome")[0])
        except ObjectNotFoundException:
            pass

        if dome:

            def syncBegin():
                self.out("=" * 40)
                self.out("synchronizing dome slit ...", end="")

            def syncComplete():
                self.out("OK")

            dome.syncBegin += syncBegin
            dome.syncComplete += syncComplete

        self.out(40 * "=")
        self.out("Taking %d %s frame[s]" % (options.frames, imagetype.upper()))
        self.out("Shutter: %s" % options.shutter)
        self.out("Interval between frames: %.3fs" % options.interval)
        if camera.isCooling():
            self.out("Cooling enabled, setpoint: %.3f oC" % camera.getSetPoint())
        else:
            self.out("Cooling disabled.")

        self.out("Current CCD temperature: %.3f oC" % camera.getTemperature())

        if options.binning:
            self.out("Binning: %s" % options.binning)
        else:
            self.out("No binning")

        if options.subframe:
            self.out("Subframe: %s" % options.subframe)
        else:
            self.out("Full Frame")

        def changeFilter(f):
            if options.filter is not None and self.wheel:
                self.out(40 * "=")
                try:
                    self.out("Changing to filter %s... " % f, end="")
                    self.wheel.setFilter(f)
                    self.out("OK")
                except InvalidFilterPositionException as e:
                    self.err("ERROR. Couldn't move filter wheel to %s. (%s)" % (f, e))
                    self.exit()

        # finally, expose
        start = time.time()

        try:
            try:
                if filterList:
                    for f in range(len(filterList)):
                        changeFilter(filterList[f])

                        if (options.interval > 0) and (1 <= f < (len(filterList))):
                            self.out("=" * 40)
                            self.out(
                                "waiting %.2f s before next frame..." % options.interval
                            )
                            time.sleep(options.interval)

                        camera.expose(
                            exptime=expTimes[f],
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
                        exptime=expTimes[0],
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

            except IOError as e:
                self.err("Error trying to take exposures (%s)" % str(e))
            except Exception as e:
                self.err("Error trying to take exposures. (%s)" % printException(e))
        finally:
            self.out(40 * "=")
            self.out("Total time: %.3fs" % (time.time() - start))
            self.out(40 * "=")
            self.out("%s" % time.strftime("%c"))
            self.out(40 * "=")


def main():
    cli = ChimeraCam()
    cli.run(sys.argv)
    cli.wait()


if __name__ == "__main__":
    main()
