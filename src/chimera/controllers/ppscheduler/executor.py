
from chimera.controllers.scheduler.handlers import (ExposeHandler, PointHandler,
                                                    AutoFocusHandler, PointVerifyHandler)
from chimera.controllers.scheduler.model import Expose, Point, AutoFocus, PointVerify
from chimera.controllers.scheduler.handlers import ActionHandler
from chimera.controllers.scheduler.status import SchedulerStatus

from chimera.core.exceptions import ObjectNotFoundException, ProgramExecutionAborted, ProgramExecutionException

import chimera.core.log
import logging
import threading
import time

log = logging.getLogger(__name__)


class ProgramExecutor(object):

    def __init__ (self, controller):

        self.currentHandler = None
        self.currentAction  = None
        
        self.mustStop = threading.Event()
        
        self.controller = controller
        self.actionHandlers = {Expose     : ExposeHandler,
                               Point      : PointHandler,
                               AutoFocus  : AutoFocusHandler,
                               PointVerify: PointVerifyHandler}

    def __start__ (self):
        for handler in self.actionHandlers.values():
            self._injectInstrument(handler)

    def execute(self, program):

        self.mustStop.clear()
        
        for action in program.actions:

            # aborted?
            if self.mustStop.isSet():
                raise ProgramExecutionAborted()

            t0 = time.time()

            try:
                self.currentAction = action
                self.currentHandler = self.actionHandlers[type(action)]

                logMsg = str(self.currentHandler.log(action))
                log.debug("[start] %s " % logMsg)
                self.controller.actionBegin(action, logMsg)

                self.currentHandler.process(action)

                # instruments just returns in case of abort, so we need to check handler
                # returned 'cause of abort or not
                if self.mustStop.isSet():
                    self.controller.actionComplete(action, SchedulerStatus.ABORTED)
                    raise ProgramExecutionAborted()
                else:
                    self.controller.actionComplete(action, SchedulerStatus.OK)

            except ProgramExecutionException, e:
                self.controller.actionComplete(action, SchedulerStatus.ERROR)
                raise
            except KeyError:
                log.debug("No handler to %s action. Skipping it" % action)
            finally:
                log.debug("[finish] took: %f s" % (time.time() - t0))

    def stop(self):
        if self.currentHandler:
            self.mustStop.set()
            self.currentHandler.abort(self.currentAction)

    def _injectInstrument(self, handler):
        if not issubclass(handler, ActionHandler):
            return

        if not hasattr(handler.process, "__requires__"):
            return
        
        for instrument in handler.process.__requires__:
            try:
                setattr(handler, instrument,
                        self.controller.getManager().getProxy(self.controller[instrument]))
            except ObjectNotFoundException, e:
                log.error("No instrument to inject on %s handler" % handler)
