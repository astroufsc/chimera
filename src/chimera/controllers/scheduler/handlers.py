import copy

from chimera.controllers.imageserver.imagerequest import ImageRequest
from chimera.core.exceptions import ProgramExecutionException, print_exception
from chimera.util.position import Epoch


def requires(instrument):
    """Simple dependency injection mechanism. See ProgramExecutor"""

    def requires_deco(func):
        if hasattr(func, "__requires__"):
            func.__requires__.append(instrument)
        else:
            func.__requires__ = [instrument]
        return func

    return requires_deco


class ActionHandler(object):

    @staticmethod
    def process(action):
        pass

    @staticmethod
    def abort(action):
        pass

    @staticmethod
    def log(action):
        return str(action)


class PointHandler(ActionHandler):

    @staticmethod
    @requires("telescope")
    @requires("dome")
    @requires("rotator")
    def process(action):
        telescope = PointHandler.telescope
        dome = PointHandler.dome
        rotator = PointHandler.rotator

        try:
            # First slew telescope to given position (or none)
            if action.target_ra_dec is not None:
                ra_dec = action.target_ra_dec
                # If epoch is not J2000, convert to J2000
                if ra_dec.epoch is None or ra_dec.epoch != Epoch.J2000:
                    ra_dec = ra_dec.to_epoch(Epoch.J2000)
                telescope.slew_to_ra_dec(
                    ra_dec.ra, ra_dec.dec, 2000.0
                )  # epoch is always 2000.0 for pointing
            elif action.target_alt_az is not None:
                telescope.slew_to_alt_az(
                    action.target_alt_az.alt, action.target_alt_az.az
                )
            elif action.target_name is not None:
                telescope.slew_to_object(action.target_name)

            # After slewing apply any given offset
            if action.offset_ns is not None:
                if action.offset_ns.arcsec > 0.0:
                    telescope.move_north(action.offset_ns.arcsec)
                else:
                    telescope.move_south(-action.offset_ns.arcsec)

            if action.offset_ew is not None:
                if action.offset_ew.arcsec > 0.0:
                    telescope.move_west(action.offset_ew.arcsec)
                else:
                    telescope.move_east(-action.offset_ew.arcsec)

            # If dome azimuth is given, point there.
            if action.dome_tracking is not None:
                if action.dome_tracking:
                    dome.track()
                else:
                    dome.stand()
            if action.dome_az is not None:
                dome.slew_to_az(action.dome_az)

            # If rotator position angle is given, set it.
            if action.pa is not None:
                rotator.move_to(action.pa)

        except Exception as e:
            raise ProgramExecutionException(str(e))

    @staticmethod
    def abort(action):
        # use newer Proxies as Proxies cannot be shared between threads
        telescope = copy.copy(PointHandler.telescope)
        dome = copy.copy(PointHandler.dome)

        telescope.abort_slew()
        dome.abort_slew()

    @staticmethod
    def log(action):

        offset_ns_str = (
            ""
            if action.offset_ns is None
            else (
                f" north {action.offset_ns}"
                if action.offset_ns > 0
                else f" south {abs(action.offset_ns)}"
            )
        )
        offset_ew_str = (
            ""
            if action.offset_ew is None
            else (
                f" west {abs(action.offset_ew)}"
                if action.offset_ew > 0
                else f" east {abs(action.offset_ew)}"
            )
        )

        offset = (
            ""
            if action.offset_ns is None and action.offset_ew is None
            else f" offset:{offset_ns_str}{offset_ew_str}"
        )

        position_angle_str = "" if action.pa is None else f" PA: {action.pa}"

        if action.target_ra_dec is not None:
            return f"slewing telescope to (ra dec) {action.target_ra_dec}{offset} ({action.target_ra_dec.epoch if action.target_ra_dec.epoch else ''}){position_angle_str}"
        elif action.target_alt_az is not None:
            return f"slewing telescope to (alt az) {action.target_alt_az}{offset}{position_angle_str}"
        elif action.target_name is not None:
            return f"slewing telescope to (object) {action.target_name}{offset}{position_angle_str}"
        elif offset != "":
            return f"applying telescope{offset}{position_angle_str}"
        else:
            if action.dome_tracking is None:
                tracking = "left AS IS"
            elif action.dome_tracking:
                tracking = "STARTED"
            else:
                tracking = "STOPPED"
            return f"dome tracking {tracking}"


class ExposeHandler(ActionHandler):

    @staticmethod
    @requires("camera")
    @requires("filterwheel")
    def process(action):

        camera = ExposeHandler.camera
        filterwheel = ExposeHandler.filterwheel

        # not considered in abort handling (should be fast enough to wait!)
        if action.filter is not None:
            filterwheel.set_filter(str(action.filter))

        ir = ImageRequest(
            frames=int(action.frames),
            exptime=float(action.exptime),
            shutter=str(action.shutter),
            type=str(action.image_type),
            filename=str(action.filename),
            object_name=str(action.object_name),
            window=action.window,
            binning=action.binning,
            wait_dome=action.wait_dome,
            compress_format=action.compress_format,
        )

        ir.headers += [
            ("PROGRAM", str(action.program.name), "Program Name"),
            ("PROG_PI", str(action.program.pi), "Principal Investigator"),
        ]

        try:
            camera.expose(ir)
        except Exception as e:
            print_exception(e)
            raise ProgramExecutionException("Error while exposing")

    @staticmethod
    def abort(action):
        camera = copy.copy(ExposeHandler.camera)
        camera.abort_exposure()

    @staticmethod
    def log(action):
        return f"exposing: filter={str(action.filter)} exptime={str(action.exptime)} frames={str(action.frames)} type={str(action.image_type)}"


class AutoFocusHandler(ActionHandler):

    @staticmethod
    @requires("autofocus")
    def process(action):
        autofocus = AutoFocusHandler.autofocus

        try:
            autofocus.focus(
                exptime=action.exptime,
                binning=action.binning,
                window=action.window,
                start=action.start,
                end=action.end,
                step=action.step,
                filter=action.filter,
            )
        except Exception as e:
            print_exception(e)
            raise ProgramExecutionException("Error while autofocusing")

    @staticmethod
    def abort(action):
        autofocus = copy.copy(AutoFocusHandler.autofocus)
        autofocus.abort()


class AutoFlatHandler(ActionHandler):

    @staticmethod
    @requires("autoflat")
    def process(action):
        autoflat = AutoFlatHandler.autoflat

        if action.binning is None:
            request = {"binning": "1x1"}
        else:
            request = {"binning": action.binning}

        try:
            autoflat.get_flats(action.filter, n_flats=action.frames, request=request)
        except Exception as e:
            print_exception(e)
            raise ProgramExecutionException("Error trying to take flats")

    @staticmethod
    def abort(action):
        skyflat = copy.copy(AutoFlatHandler.autoflat)
        skyflat.abort()


class PointVerifyHandler(ActionHandler):

    @staticmethod
    @requires("point_verify")
    def process(action):

        # FIXME: better pv interface
        pv = PointVerifyHandler.point_verify

        try:
            if action.here is not None:
                pv.point_verify()
            elif action.choose is not None:
                pv.choose()
        except Exception as e:
            raise ProgramExecutionException(str(e))

    @staticmethod
    def abort(action):
        pass
