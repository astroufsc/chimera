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

import SocketServer
import SimpleXMLRPCServer

import socket
import sys

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.location import Location
from chimera.core.exceptions import ObjectNotFoundException

from chimera.util.coord import Coord
from chimera.util.position import Position
#from chimera.controllers.imageserver.imageuri import ImageURI

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


class ChimeraXMLDispatcher:
    
    def __init__ (self, ctrl):
        self._ctrl = ctrl
        self._proxyCache = {}
    
    def _dispatch (self, request, params):
        # this dispatcher expects methods names like ClassName.instance_name.method
        
        try:
            cls, instance, method = request.split(".")
        except ValueError:
            raise ValueError("Invalid Request")

        loc = Location(cls=cls, name=instance)
        
        if loc not in self._proxyCache:
            try:
                obj = self._ctrl.getManager().getProxy(loc)
                self._proxyCache[loc] = obj
            except ObjectNotFoundException:
                raise ValueError("Object Not Found")

        obj = self._proxyCache[loc]
        obj._transferThread()
        
        handle = getattr(obj, method)
        
        try:
            ret = handle(*params)
        except AttributeError:
            raise ValueError("Method not found,")

        # do some conversions to help Java XML Server

        if isinstance(ret, (tuple, list)):

            newret = []

            for arg in ret:
                if isinstance(arg, (Position, Coord)):
                    newret.append(str(arg))
                elif isinstance(arg, Location):
                    if "hash" in arg.config:
                        newret.append(str(arg.config["hash"]))
                    else:
                        newret.append(str(ret))
                else:
                    newret.append(arg)

            return newret

        else:
            if isinstance(ret, (Position, Coord)):
                    return str(ret)
            elif isinstance(ret, Location):
                if "hash" in ret.config:
                    return str(ret.config["hash"])
                else:
                    return str(ret)
            else:
                return ret

    
class XMLRPC(ChimeraObject):

    __config__ = {"host": "localhost",
                  "port": 7667}

    def __init__(self):
        ChimeraObject.__init__(self)

        self._srv = None
        self._dispatcher = None
        
    def isAlive (self):
        return True

    def getListOf (self, cls):
        locations = filter(lambda loc: loc.cls == cls, self.getManager().getResources())
        return ["%s.%s" % (loc.cls, loc.name) for loc in locations]

    def __start__(self):
        self._dispatcher = ChimeraXMLDispatcher(self)
        try:
            self._srv = ThreadingXMLRPCServer ((self["host"], self["port"]))
            self._srv.register_introspection_functions ()
            self._srv.register_instance (self._dispatcher)
            self._srv.register_function(self.isAlive, 'Chimera.isAlive')
            self._srv.register_function(self.getListOf, 'Chimera.getListOf')            
            return True
        except socket.error, e:
            self.log.error ("Error while starting Remote server (%s)" % e)
        
    def control (self):
        
        if self._srv != None:
            self.log.info("Starting XML-RPC server at http://%s:%d" % (self["host"], self["port"])) 
            self._srv.serve_forever ()
                    
