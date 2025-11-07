import io
import logging
import logging.handlers
import os.path

from rich.logging import RichHandler

from chimera.core.constants import (
    MANAGER_DEFAULT_HOST,
    MANAGER_DEFAULT_PORT,
    SYSTEM_CONFIG_DIRECTORY,
    SYSTEM_CONFIG_LOG_NAME,
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

console_handler = RichHandler()
root.addHandler(console_handler)


def set_console_level(level: int):
    console_handler.setLevel(level)


try:
    file_handler = logging.handlers.RotatingFileHandler(
        SYSTEM_CONFIG_LOG_NAME, maxBytes=5 * 1024 * 1024, backupCount=10
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(flt)
    root.addHandler(file_handler)
except Exception as e:
    root.warning(f"Couldn't start Log System FileHandler ({e})")
