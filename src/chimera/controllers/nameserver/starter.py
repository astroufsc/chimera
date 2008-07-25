from chimera.core.chimeraobject import ChimeraObject
from chimera.controllers.nameserver.server import Server
from Pyro.naming import NameServerLocator, main
from Pyro.errors import NamingError
from Pyro.core import PyroURI
import threading
from chimera.core.constants import MANAGER_DEFAULT_HOST
from chimera.core.lock     import lock

import logging
from chimera.core.log import logging

log = logging.getLogger(__name__)

class Starter(ChimeraObject):
    
    __config__ = {'host':   MANAGER_DEFAULT_HOST}
    
    def __init__(self):
        ChimeraObject.__init__(self)
        self._ns = None
        self._server = None
        self.__gettingNS = False
        self.__makingNS = False
        self.__nsFails = 0
        self.__localNS = False
        
    def __start__(self):
        self._getNS()
        self.setHz(1.0/10.0)    #give nameserver ten seconds to start
        
    def __stop__(self):
        #FIXME: Need to unregister us from nameserver
        if self._server:
            log.info('Stopping nameserver')
            self._server.stop()
    
    def _getNS(self):
        if not self.__gettingNS:
            self.__gettingNS = True
            locator = NameServerLocator()
            try:
                self._ns = locator.getNS()
            except NamingError:
                self._makeNS()
            self.__gettingNS = False
    
    def _makeNS(self):
        if not self.__makingNS:
            self.__makingNS = True
            if self.__localNS and self._server != None:
                if self._server.isAlive():
                    self.__makingNS=False
                    return
            self.__localNS = True
            self._server = Server(host=self['host'])
            self._server.start()
            self.__makingNS = False
    
    def _register(self, name, object, guid=None, mgr=None):
        if mgr == None:
            mgr=self.getManager()
        if guid == None:
            guid=object.getGUID()
        guid = guid.__str__()
        try:
            pURI=PyroURI(self['host'], guid, mgr.getPort())
            pNAME = name + '-' + self['host'].replace('.', '-') + '-' + mgr.getPort().__str__()
            log.debug('Registering ' + pNAME + ' as ' + pURI.__str__())
            self._ns.register(pNAME, pURI)
        except NamingError:
            #We don't care -- that means that we are already registered
            pass
        
    def _useNS(self):
        try:
            self._ns.createGroup(':chimera')
            self._ns.createGroup(':chimera.nameservers')
            self._ns.createGroup(':chimera.managers')
        except NamingError:
            #We don't care -- that means that we are already registered
            pass
        mgr = self.getManager()
        self._register(':chimera.nameservers.ns', self, mgr)
        self._register(':chimera.managers.manager', mgr, mgr)
                
    @lock
    def control (self):
        if self.__gettingNS:
            log.debug('Not checking NS -- NS get in progress.')
        else:
            log.debug('Checking NS')
            if self._ns == None:
                log.debug('Need initial NS')
                self.setHz(1)
                self._getNS()
            else:
                log.debug('Checking NS proxy')
                self._ns._transferThread()
                try:
                    self._ns.ping()
                except NamingError:
                    log.debug('NS Pings Down!')
                    self._getNS()
                    self.setHz(1.0/2.0)
                    self.__nsFails=self.__nsFails+1
                    return True
                log.debug('NS Pings Up!')
                self.__nsFails = 0
                self.setHz(1.0/15.0)
                self._useNS()
        return True
