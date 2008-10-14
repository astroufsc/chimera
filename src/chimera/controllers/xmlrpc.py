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
import select
import threading

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.location import Location
from chimera.core.exceptions import ObjectNotFoundException

from chimera.util.coord import Coord
from chimera.util.position import Position

from Pyro.util import getPyroTraceback


class ThreadingXMLRPCServer (SocketServer.ThreadingTCPServer,
                             SimpleXMLRPCServer.SimpleXMLRPCDispatcher):

    def __init__(self, addr,
                 requestHandler=SimpleXMLRPCServer.SimpleXMLRPCRequestHandler,
                 logRequests=1, allow_none=True):

        self.logRequests = logRequests

        if sys.version_info[:2] == (2,5):
            SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self, False, sys.getdefaultencoding())
        else:
            SimpleXMLRPCServer.SimpleXMLRPCDispatcher.__init__(self)

        SocketServer.ThreadingTCPServer.__init__(self, addr, requestHandler)
        
        self.closed = False
    
    def shutdown(self):
        self.closed = True
    
    def get_request(self):
        inputObjects = []
        while not inputObjects and not self.closed:
            inputObjects = select.select([self.socket], [], [], 0.2)[0]
            try:
                return self.socket.accept()
            except socket.error:
                raise

class serverThread(threading.Thread):
    
    def __init__(self, server):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.server = server
        self.server.socket.setblocking(0)
        self.closed = False
    
    def shutdown(self):
        self.closed = True
        self.server.shutdown()
    
    def run(self):
        while not self.closed:
            self.server.handle_request()

class ChimeraXMLDispatcher:
    
    def __init__ (self, ctrl):
        self._ctrl = ctrl
        self._proxyCache = {}
    
    def _dispatch (self, request, params):
        # this dispatcher expects methods names like ClassName.instance_name.method
        
        if self._ctrl['debug']:
            self._ctrl.log.debug('XML Request for %s : %s' % (str(request),str(params)))
        
        try:
            cls, instance, method = request.split(".")
        except ValueError:
            if self._ctrl['debug']:
                self._ctrl.log.debug('ValueError:Invalid Request')
            raise ValueError("Invalid Request")

        loc = Location(cls=cls, name=instance)
        
        if loc not in self._proxyCache:
            try:
                obj = self._ctrl.getManager().getProxy(loc)
                self._proxyCache[loc] = obj
            except ObjectNotFoundException:
                if self._ctrl['debug']:
                    self._ctrl.log.debug('ObjectNotFoundException:Object Not Found')
                raise ValueError("Object Not Found")
        else:
            try:
                obj = self._proxyCache[loc]
                obj._transferThread()
                if not obj.ping():
                    raise Exception()   #We need to remake the proxy
            except:
                try:
                    obj = self._ctrl.getManager().getProxy(loc)
                    self._proxyCache[loc] = obj
                except ObjectNotFoundException:
                    if self._ctrl['debug']:
                        self._ctrl.log.debug('ObjectNotFoundException:Object Not Found')
                    raise ValueError("Object Not Found")
        
        handle = getattr(obj, method)
        obj._release()
        
        try:
            ret = handle(*params)
        except AttributeError:
            if self._ctrl['debug']:
                self._ctrl.log.debug('AttributeError:Method not found')
            raise ValueError("Method not found")
        except Exception, e:
            if self._ctrl['debug']:
                print ''.join(getPyroTraceback(e))
                self._ctrl.log.debug('Other Error <%s>: %s' % (type(e),str(e)))
            raise

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
                elif isinstance(arg, type(None)):
                    newret.append(True)
                else:
                    newret.append(arg)

            if self._ctrl['debug']:
                self._ctrl.log.debug('Returning: %s' % str(newret))
                
            return newret

        else:
            if isinstance(ret, (Position, Coord)):
                if self._ctrl['debug']:
                    self._ctrl.log.debug('Returning: %s' % str(ret))
                    return str(ret)
            elif isinstance(ret, Location):
                if "hash" in ret.config:
                    if self._ctrl['debug']:
                        self._ctrl.log.debug('Returning: %s' % str(ret.config["hash"]))
                    return str(ret.config["hash"])
                else:
                    if self._ctrl['debug']:
                        self._ctrl.log.debug('Returning: %s' % str(ret))
                    return str(ret)
            elif isinstance(ret, type(None)):
                if self._ctrl['debug']:
                    self._ctrl.log.debug('Returning: %s' % str(True))
                return True
            else:
                if self._ctrl['debug']:
                    self._ctrl.log.debug('Returning: %s' % str(ret))
                return ret

    
class XMLRPC(ChimeraObject):

    __config__ = {"host": "",
                  "port": 7667,
                  'debug': False,    #Log all XMLRPC communications
                  }

    def __init__(self):
        ChimeraObject.__init__(self)

        self._srv = None
        self._dispatcher = None
        self._srvThread = None
        self.host = None
        
    def isAlive (self):
        return True

    def getListOf (self, cls):
        locations = filter(lambda loc: loc.cls == cls, self.getManager().getResources())
        return ["%s.%s" % (loc.cls, loc.name) for loc in locations]

    def __start__(self):
        self._dispatcher = ChimeraXMLDispatcher(self)
        self.host = self["host"]
        if not self.host:
            self.host=self.getManager().getHostname()
        try:
            self._srv = ThreadingXMLRPCServer ((self.host, self["port"]))
            self._srv.register_introspection_functions ()
            self._srv.register_instance (self._dispatcher)
            self._srv.register_function(self.isAlive, 'Chimera.isAlive')
            self._srv.register_function(self.getListOf, 'Chimera.getListOf')            
            return True
        except socket.error, e:
            self.log.error ("Error while starting Remote server (%s)" % e)

    def __stop__(self):
        self.log.info('Shutting down XMLRPC server at http://%s:%d' % (self.host, self["port"]))
        self._srvThread.shutdown()
        
    def control (self):
        
        if self._srv != None:
            self.log.info("Starting XML-RPC server at http://%s:%d" % (self.host, self["port"])) 
            self._srvThread = serverThread(self._srv)
            self._srvThread.start()
            
        return False
