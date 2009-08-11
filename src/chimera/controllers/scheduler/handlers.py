from chimera.core.exceptions import ProgramExecutionException, printException
from chimera.controllers.imageserver.imagerequest import ImageRequest

import chimera.core.log
import logging

log = logging.getLogger(__name__)

def requires(instrument):
    """Simple dependecy injection mechanism. See ProgramExecutor"""

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

class PointHandler(ActionHandler):

    @staticmethod
    @requires("telescope")    
    def process(action):
        telescope = PointHandler.telescope

        if action.targetRaDec is not None:
            log.debug("[slewing telescope to %s]" % action.targetRaDec)
            telescope.slewToRaDec(action.targetRaDec)
        if action.targetAltAz is not None:
            log.debug("[slewing telescope to %s]" % action.targetRaDec)
            telescope.slewToAltAz(action.targetAltAz)
        elif action.targetName:
            log.debug("[slewing telescope to %s]" % action.targetName)
            telescope.slewToObject(action.targetName)
        else:
            raise ProgramExecutionException("Invalid slew action.")

        log.debug('[slew complete]')
        
class ExposeHandler(ActionHandler):

    @staticmethod
    @requires("camera")
    @requires("filterwheel")
    def process(action):

        camera = ExposeHandler.camera
        filterwheel = ExposeHandler.filterwheel

        if action.filter is not None:
            log.debug("[setting filter to %s]" % action.filter)
            filterwheel.setFilter(str(action.filter))
            log.debug("[filter set complete]")
            
        ir = ImageRequest(frames   = int(action.frames),
                          exptime  = float(action.exptime),
                          shutter  = str(action.shutter),
                          type     = str(action.imageType),
                          filename = str(action.filename),
                          object_name = str(action.objectName),
                          window = action.window,
                          binning = action.binning,
                          wait_dome = True)

        ir.headers += [("PROGRAM", str(action.program.name), "Program Name"),
                       ("PROG_PI", str(action.program.pi), "Principal Investigator")]

        log.info("[exposing: %s]" % ir)

        try:
            camera.expose(ir)
        except Exception, e:
            printException(e)
            raise ProgramExecutionException("Error while exposing")
            
        log.info("[expose complete]")    

class AutoFocusHandler(ActionHandler):

    @staticmethod
    @requires("autofocus")
    def process(action):
        autofocus = AutoFocusHandler.autofocus

        try:
            autofocus.focus (filter=action.filter,
                             exptime=action.exptime,
                             binning=action.binning,
                             window=action.window,
                             start=action.start,
                             end=action.end,
                             step=action.step)
        except Exception, e:
            printException(e)
            raise ProgramExecutionException("Error while autofocusing")

class PointVerifyHandler(ActionHandler):

    @staticmethod
    @requires("point_verify")
    def process(action):

        # FIXME: better pv interface
        pv = PointVerifyHandler.point_verify

        if action.here is not None:
            pv.here()
        elif action.choose is not None:
            pv.choose()
        else:
            raise ProgramExecutionException("Invalid point verify action.")
