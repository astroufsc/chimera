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

from chimera.core.interface import Interface
from chimera.core.event import event

class IDome (Interface):

    __options__ = {"driver": "/DomeLNA40cm/dome",
                   "telescope": "/Telescope/0",
                   "time_res": 2, # time resolution - how often we check telescope position
                   "az_res": 2, # move the dome when telescope moves more than position_res degress
                   "mode": "stand"} # operation mode = track / stand
    
    # AK - ver classes location -
    # /A/B
    # A nome do driver precisa ser informado por quem criar a cupula
    # B nome default, se eu nao der um nome ele poe esse
    
    # methods
    def isSlewing (self):
        pass

    def abortSlew (self):
        pass

    def getAz (self):
        pass

    def sletToAz (self):
        pass
    
    # events

    @event
    def slewComplete (self, position):
        pass

    @event
    def abortComplete (self, position):
        pass


# AK - quem fala com isso eh o instrumento
class IDomeDriver (Interface):

    __options__ = {"device": "/dev/ttyS1",
                   "az_res": 2,  # dome position resolution
                   "slew_timeout" : 120,
                   "abort_timeout": 60,                   
                   "open_timeout" : 20,
                   "close_timeout": 20,
                   } 
  
    # methods

    def open(self):
        pass

    def close(self):
        pass

    def isSlewing (self):
        pass

    def abortSlew(self):
        pass

    def getAz(self):
        pass

    def slewToAz(self):
        pass


    # events
    
    @event
    def slewComplete (self, position):
        pass

    @event
    def abortComplete (self, position):
        pass
    
