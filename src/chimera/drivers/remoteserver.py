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

import SocketServer
import SimpleXMLRPCServer

import socket
import logging
import new
import sys

from chimera.core.lifecycle import BasicLifeCycle

# FIXME: handle client exit (connection abort errorrs)

class ThreadingXMLRPCServer (SocketServer.ThreadingTCPServer,
                             SimpleXMLRPCServer.SimpleXMLRPCDispatcher):

    def __init__(self, addr,
                 requestHandler=SimpleXMLRPCServer.SimpleXMLRPCRequestHandler,
                 logRequests=1):

        self.logRequests = logRequests

        if sys.version_info[:2] == (2,5):
            SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self, False, sys.getdefaultencoding())
        else:
            SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self)

        SocketServer.ThreadingTCPServer.__init__(self, addr, requestHandler)


class RemoteServer(BasicLifeCycle):

    __options__ = {"driver": "/Fake/camera",
                   "port": 1090}

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

        self.srv = None
        self.obj = None

    def init(self, config):

        self.config += config

        self.obj = self.manager.getDriver (self.config.driver, proxy=False)

        def _dispatch (self, method, params):
            method = getattr(self, params[0])
            return method(*params[1])

        self.obj._dispatch = new.instancemethod (_dispatch, self.obj, type(self.obj))

        try:
            self.srv = ThreadingXMLRPCServer (('', self.config.port))
            self.srv.register_introspection_functions ()
            self.srv.register_instance (self.obj)
            return True
        except socket.error, e:
            logging.error ("Error while starting Remote server for %s. %s" % (self.config.driver, e))
            self.srv = None
            return False

    def main (self):
        if self.srv != None:
            self.srv.serve_forever ()
        


