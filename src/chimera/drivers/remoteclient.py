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

import xmlrpclib
import socket
import logging

from chimera.core.lifecycle import BasicLifeCycle

class RemoteClient(BasicLifeCycle):

    __options__ = {"host": "150.16.3047",
                   "port": 1090}

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

        self.proxy = None

    def init(self, config):
        self.config += config

        url = "http://%s:%d/RPC2" % (self.config.host, self.config.port)

        self.proxy = xmlrpclib.ServerProxy(url)

        return True

    def __getattr__ (self, attr):
        return RemoteMethodWrapper (self.proxy.__request, attr)


class RemoteMethodWrapper(object):

    def __init__(self, send, name):
        self.__send = send
        self.__name = name
        
    def __call__(self, *args, **kwargs):
        try:
            return self.__send(self.__name, args)
        except socket.error, e:
            logging.error ("Error while calling remote method (%s). %s" % (self.__name, e))
            return False

    def __repr__ (self):
        return "<RPC Wrapper for method %s>" % self.__name
    
