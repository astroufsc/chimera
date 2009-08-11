
from chimera.controllers.scheduler.handlers import (ExposeHandler, PointHandler,
                                                    AutoFocusHandler, PointVerifyHandler)
from chimera.controllers.scheduler.model import Expose, Point, AutoFocus, PointVerify
from chimera.controllers.scheduler.handlers import ActionHandler
from chimera.core.exceptions import ObjectNotFoundException

import chimera.core.log
import logging

log = logging.getLogger(__name__)


class ProgramExecutor(object):

    def __init__ (self, controller):

        self.controller = controller
        self.actionHandlers = {Expose     : ExposeHandler,
                               Point      : PointHandler,
                               AutoFocus  : AutoFocusHandler,
                               PointVerify: PointVerifyHandler}

    def __start__ (self):
        for handler in self.actionHandlers.values():
            self._injectInstrument(handler)

    def execute(self, program):
        log.debug("[processing] %s" % str(program))
        
        for action in program.actions:
            try:
                self.actionHandlers[type(action)].process(self.controller.getManager(), action)
            except KeyError:
                log.debug("No handler to %s action. Skipping it" % action)

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
