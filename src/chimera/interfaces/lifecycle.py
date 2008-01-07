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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


from chimera.core.interface import Interface
from chimera.core.state     import State


__all__ = ['ILifeCycle']


class ILifeCycle (Interface):

    """
    Basic interface implemented by every device on the system. This
    interface provides basic life-cycle management and main loop control.

    """

    def __init__(self):
        """
        Do object initialization.

        Constructor should only do basic initialization. Shouldn't
        even 'touch' any hardware, open files or sockets. Constructor
        is called by L{Manager}.

        @note: Runs on the Manager's thread.
        @warning: This method must not block, so be a good boy/girl.
        """
        
    def __start__ (self):
        """
        Do device initialization. Open files, access drivers and
        sockets. This method it's called by Manager, just after the constructor.

        @note: Runs on the L{Manager} thread.
        @warning: This method must not block, so be a good boy/girl.
        """
        
    def __stop__ (self):
        """
        Cleanup {__start__} actions.

        {__stop__} it's called by Manager when Manager is diying or
        programatically at any time (to remove an Instrument during
        system lifetime).

        @note: Runs on the Manager thread.
        @warning: This method must not block, so be a good boy/girl.
        """

    def __main__ (self):
        """
        Main control method. Implementeers could use this method to
        implement control loop functions.

        @note: This method runs on their own thread.
        """

    def getState (self):
        """
        Get the current state of the object as a L{State} enum.

        @see: L{State} for possible values.
        """

    def __setstate__ (self, state):
        """
        Internally used function to set the current state of the object.

        @see: L{State} for possible values.
        """

    def getLocation (self):
        """
        Get the current L{Location} where the object is deployed.
        """

    def __setlocation__ (self, location):
        """
        Internally used function to set the current location of the object.
        """

    def getManager (self):
        """
        Get the current Manager for this object.
        """

    def getProxy (self):
        """
        Get a Proxy for this object (usefull for callbacks)
        """
