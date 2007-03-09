#! /usr/bin/python
# -*- coding: iso8859-1 -*-

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

import time
import threading

from chimera.interfaces.lifecycle import ILifeCycle
from chimera.core.event import EventsProxy
from chimera.core.config import Config

class BasicLifeCycle(ILifeCycle):

    def __init__(self, manager):

        self.manager = manager

        # loop control
        self.timeslice = 0.5
        self.looping = False

        # term event
        self.term = threading.Event()

        # event handling
        self.__eventsProxy__ = EventsProxy(self.__events__)

        # create configuration as necessary
        self.config = Config(self.__options__)

    def init(self, config):
        pass

    def shutdown(self):
        pass

    def main(self):
            
        # FIXME: better main loop control
        
        # enter main loop
        self._main()
        
        return True

    def control(self):
        pass

    def _main(self):

        self.looping = True

        try:

            while(self.looping):

                if (self.term.isSet()):
                    self.looping = False
                    return
            
                # run control function
                self.control()

                time.sleep(self.timeslice)

        except KeyboardInterrupt, e:
            self.looping = False
            return

    def __getattr__(self, attr):
        if attr in self.__eventsProxy__:
            return self.__eventsProxy__[attr]
        else:
            raise AttributeError
        
        
