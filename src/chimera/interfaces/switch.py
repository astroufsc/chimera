# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>
from chimera.core.event import event
from chimera.core.interface import Interface
from chimera.util.enum import Enum


class SwitchStatus(Enum):
    ON = "ON"
    OFF = "OFF"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class Switch(Interface):
    """
    Interface for general switches
    """

    __config__ = {
        "device": None,
        "switch_timeout": None,  # Maximum number of seconds to wait for state change
    }

    def switch_on(self) -> bool:
        """
        Switch on.

        @return: True if successful, False otherwise
        @rtype: bool
        """
        ...

    def switch_off(self) -> bool:
        """
        Switch off.

        @return: True if successful, False otherwise
        @rtype: bool
        """
        ...

    def is_switched_on(self) -> bool:
        """
        Get current state of switch

        @return: True if On, False otherwise
        @rtype: bool
        """
        ...

    @event
    def switched_on(self) -> None:
        """
        Event triggered when switched ON

        """
        ...

    @event
    def switched_off(self) -> None:
        """
        Event triggered when switched OFF

        """
        ...


class SwitchState(Switch):
    """
    For switches that have status information
    """

    def status(self) -> SwitchStatus:
        """
        :return: state from SwitchStatus Enum
        """
        ...
