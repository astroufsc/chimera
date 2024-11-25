#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
from chimera.core.event import event
from chimera.core.interface import Interface
from chimera.util.enum import Enum

SwitchStatus = Enum("ON", "OFF", "UNKNOWN", "ERROR")


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
