# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from typing import Any

from chimera.core.event import event
from chimera.core.exceptions import ChimeraException
from chimera.core.interface import Interface


class StarNotFoundException(ChimeraException):
    pass


class FocusNotFoundException(ChimeraException):
    pass


class Autofocus(Interface):
    __config__ = {
        "camera": "/Camera/0",
        "filterwheel": "/FilterWheel/0",
        "focuser": "/Focuser/0",
        "max_tries": 3,
    }

    def focus(
        self,
        filter: str | None = None,
        exptime: float | None = None,
        binning: str | None = None,
        window: str | None = None,
        start: int = 2000,
        end: int = 6000,
        step: int = 500,
        minmax: tuple[float, float] | None = None,
        debug: bool = False,
    ) -> Any:
        """
        Focus
        """
        ...

    def stop(self) -> None:
        """
        Abort a running focus() ASAP: stop the current exposure and return
        the focuser to its start position. No-op if nothing is running.
        Runs concurrently with focus(), so it must not take the focus lock.
        """
        ...

    @event
    def step_complete(self, position: int, star: dict[str, Any], frame: str) -> None:
        """Raised after every step in the focus sequence with
        information about the last step.
        """
        ...
