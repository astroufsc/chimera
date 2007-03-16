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

from catalog import Object

class Observation(object):

    def __init__(self, target = None):

        self.frame_type = None
        self.obj = Object()
        self.nexp = 0
        self.exptime = 0
        self.filtername = 0
        #self.path = ""

        if (target):
            self.fromList(target)

    def fromList(self, target):
        self.frame_type = target[0]
        self.obj = Object(target[1], target[2], target[3])
        self.nexp = target[4]
        self.exptime = target[5]
        self.filtername = target[6]
        #self.path = target[7]



    def __repr__(self):           
        s = "%s %s %s\n#%s exposures of %s seconds each.\n" % (self.obj.name, self.obj.ra, self.obj.dec, self.nexp, self.exptime)
        return s
        
class ObservationPlan(object):

    def __init__(self, filename):

        self.filename = filename

        self.observations = []

    def __len__(self):
        return len(self.observations)

    def __iter__(self):
        return iter(self.observations)

    def addObservation(self, obs):
        self.observations.append(obs)

