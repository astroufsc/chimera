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

    def switchOn(self):
        """
        Switch on.

        @return: True if successful, False otherwise
        @rtype: bool
        """

    def switchOff(self):
        """
        Switch off.

        @return: True if successful, False otherwise
        @rtype: bool
        """

    def isSwitchedOn(self):
        """
        Get current state of switch

        @return: True if On, False otherwise
        @rtype: bool
        """

    @event
    def switchedOn(self):
        """
        Event triggered when switched ON

        """

    @event
    def switchedOff(self):
        """
        Event triggered when switched OFF

        """


class SwitchState(Switch):
    """
    For switches that have status information
    """

    def status(self):
        """
        :return: state from SwitchStatus Enum
        """
