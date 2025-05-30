import io
import logging
import logging.handlers
import sys
import os.path

from chimera.core.constants import (
    SYSTEM_CONFIG_LOG_NAME,
    SYSTEM_CONFIG_DIRECTORY,
    MANAGER_DEFAULT_HOST,
    MANAGER_DEFAULT_PORT,
)

from chimera.core.exceptions import print_exception


__all__ = ["set_console_level"]


class ChimeraFormatter(logging.Formatter):

    def __init__(self, fmt, datefmt):
        logging.Formatter.__init__(self, fmt, datefmt)

    def formatException(self, exc_info):  # noqa: N802
        stream = io.StringIO()
        print_exception(exc_info[1], stream=stream)

        try:
            return stream.getvalue()
        finally:
            stream.close()


class ChimeraFilter(logging.Filter):

    def __init__(self):
        # Explicitely set this filter for all loggers.
        logging.Filter.__init__(self, name="")

    def filter(self, record):
        # Get the manager:port info
        record.origin = (
            "[" + MANAGER_DEFAULT_HOST + ":" + str(MANAGER_DEFAULT_PORT) + "]"
        )
        return True


try:
    if not os.path.exists(SYSTEM_CONFIG_DIRECTORY):
        os.mkdir(SYSTEM_CONFIG_DIRECTORY)
except Exception:
    pass

root = logging.getLogger("chimera")
root.setLevel(logging.DEBUG)
root.propagate = False

fmt = ChimeraFormatter(
    fmt="%(asctime)s.%(msecs)d %(origin)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
)

flt = ChimeraFilter()

consoleHandler = logging.StreamHandler(sys.stderr)
consoleHandler.setFormatter(fmt)
consoleHandler.setLevel(logging.WARNING)
consoleHandler.addFilter(flt)
root.addHandler(consoleHandler)


def set_console_level(level):
    consoleHandler.setLevel(level)


try:
    fileHandler = logging.handlers.RotatingFileHandler(
        SYSTEM_CONFIG_LOG_NAME, maxBytes=5 * 1024 * 1024, backupCount=10
    )
    fileHandler.setFormatter(fmt)
    fileHandler.setLevel(logging.DEBUG)
    fileHandler.addFilter(flt)
    root.addHandler(fileHandler)
except Exception as e:
    root.warning(f"Couldn't start Log System FileHandler ({e})")
