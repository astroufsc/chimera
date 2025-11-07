import logging
import threading
import time

from chimera.controllers.scheduler.handlers import (
    ActionHandler,
    AutoFlatHandler,
    AutoFocusHandler,
    ExposeHandler,
    PointHandler,
    PointVerifyHandler,
)
from chimera.controllers.scheduler.model import (
    AutoFlat,
    AutoFocus,
    Expose,
    Point,
    PointVerify,
)
from chimera.controllers.scheduler.status import SchedulerStatus
from chimera.core.exceptions import (
    ObjectNotFoundException,
    ProgramExecutionAborted,
    ProgramExecutionException,
)

log = logging.getLogger(__name__)


class ProgramExecutor:
    def __init__(self, controller):
        self.current_handler = None
        self.current_action = None

        self.must_stop = threading.Event()

        self.controller = controller
        self.action_handlers = {
            Expose: ExposeHandler,
            Point: PointHandler,
            AutoFocus: AutoFocusHandler,
            AutoFlat: AutoFlatHandler,
            PointVerify: PointVerifyHandler,
        }

    def __start__(self):
        for handler in list(self.action_handlers.values()):
            self._inject_instrument(handler)

    def execute(self, program):
        self.must_stop.clear()

        for action in program.actions:
            # aborted?
            if self.must_stop.is_set():
                raise ProgramExecutionAborted()

            t0 = time.time()

            try:
                self.current_action = action
                self.current_handler = self.action_handlers[type(action)]

                log_msg = str(self.current_handler.log(action))
                log.debug(f"[start] {log_msg} ")
                self.controller.action_begin(action, log_msg)

                self.current_handler.process(action)

                # instruments just returns in case of abort, so we need to check handler
                # returned 'cause of abort or not
                if self.must_stop.is_set():
                    self.controller.action_complete(action, SchedulerStatus.ABORTED)
                    raise ProgramExecutionAborted()
                else:
                    self.controller.action_complete(action, SchedulerStatus.OK)

            except ProgramExecutionException:
                self.controller.action_complete(action, SchedulerStatus.ERROR)
                raise
            except KeyError:
                log.debug(f"No handler to {action} action. Skipping it")
            finally:
                log.debug("[finish] took: %f s" % (time.time() - t0))

    def stop(self):
        if self.current_handler:
            self.must_stop.set()
            self.current_handler.abort(self.current_action)

    def _inject_instrument(self, handler):
        if not issubclass(handler, ActionHandler):
            return

        if not hasattr(handler.process, "__requires__"):
            return

        for instrument in handler.process.__requires__:
            try:
                setattr(
                    handler,
                    instrument,
                    self.controller.get_proxy(self.controller[instrument]),
                )
            except ObjectNotFoundException:
                log.error(f"No instrument to inject on {handler} handler")
