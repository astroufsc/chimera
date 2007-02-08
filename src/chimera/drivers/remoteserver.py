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

from SimpleXMLRPCServer import SimpleXMLRPCServer

from chimera.core.lifecycle import BasicLifeCycle

class RemoteServer(BasicLifeCycle):

    __options__ = {"host": "150.16.3047",
                   "port": 1090,
                   "driver": "/Fake/camera"}

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

        self.srv = None
        self.obj = None

    def init(self, config):

        self.config += config

        self.obj = self.manager.getDriver (self.config.driver)

        self.srv = SimpleXMLRPCServer ((self.config.host, self.config.port))
        self.srv.register_introspection_functions ()
        self.srv.register_instance (self.obj)

    def control (self):

        self.srv.serve_forever ()


