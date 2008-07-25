from Pyro.naming import *
import Pyro
import Pyro.util
import Pyro.configuration
from Pyro import core, errors

import logging
from chimera.core.log import logging

from threading import Thread

log = logging.getLogger(__name__)

class Server(Thread):
    def __init__(self, host=None):
        Thread.__init__(self)
        self.started = Pyro.util.getEventObject()
        self.host = host
        self.setDaemon(True)
            
        
    def run(self):
        nsport=Pyro.config.PYRO_NS_PORT
        bcport=Pyro.config.PYRO_NS_BC_PORT
        otherNSuri=None
        try:
            retries=Pyro.config.PYRO_BC_RETRIES
            timeout=Pyro.config.PYRO_BC_TIMEOUT
            Pyro.config.PYRO_BC_RETRIES=1
            Pyro.config.PYRO_BC_TIMEOUT=0.7
            try:
                otherNSuri=NameServerLocator().detectNS()
            except errors.PyroError:
                pass
            else:
                log.error('The Name Server appears to be already running on this segment.'
                            '(host:', otherNSuri.address, ' port:', otherNSuri.port, ')'
                            'Cannot start multiple Name Servers in the same network segment.')
                raise errors.NamingError('Cannot start multiple Name Servers in the same network segment.')

            Pyro.config.PYRO_BC_RETRIES=retries
            Pyro.config.PYRO_BC_TIMEOUT=timeout
            daemon = core.Daemon(host=self.host, port=nsport, norange=True)
        except errors.DaemonError, x:
            log.error('The Name Server appears to be already running on this host.'
                      '(or somebody else occupies our port,', nsport, ')')
            if hostname:
                log.error('It could also be that the address \'%s\' is not correct.' % hostname)
            log.error('Name Server was not started!')
            raise

        ns=NameServer()
        daemon.useNameServer(ns)
        NS_URI=daemon.connect(ns, constants.NAMESERVER_NAME)

        # Try to start the broadcast server. Binding on the magic "<broadcast>"
        # address should work, but on some systems (windows) it doesn't.
        # Therefore we first try "<broadcast>", if that fails, try "".
        self.bcserver=None
        notStartedError=""
        if daemon.validateHostnameAndIP():
            log.warn("Not starting broadcast server because of issue with daemon IP address.")
        else:
            for bc_bind in ("<broadcast>", ""):
                try:
                    self.bcserver = BroadcastServer((bc_bind, bcport), bcRequestHandler, norange=True)
                    break
                except socket.error, x:
                    notStartedError += str(x)+" "
            if not self.bcserver:
                log.error ('Cannot start broadcast server. Is somebody else occupying our broadcast port?')
                log.error ('The error(s) were:' + notStartedError.__str__())
                log.error ('Name Server was not started!')
                raise errors.NamingError("cannot start broadcast server")

        log.info('Name server listening on:' + daemon.sock.getsockname().__str__())
        if self.bcserver:
            log.info('Broadcast server listening on: '+self.bcserver.socket.getsockname().__str__())
        message = daemon.validateHostnameAndIP()
        if message:
            log.warning(message.__str__())

        ns.publishURI(NS_URI, False)

        if self.bcserver:
            self.bcserver.setNS_URI(NS_URI)
        log.info("This is the Pyro Name Server.")
        log.info("Starting on %s port %d", daemon.hostname, daemon.port)
        if self.bcserver:
            log.info("Broadcast server on port %d", bcport)
        else:
            log.warning("No Broadcast server")

        log.info('Name Server started.')
        
        self.started.set()   # signal that we've started (for external threads)

        daemon.setTimeout(20)  # XXX fixed timeout
        self.daemon=daemon

        # I use a timeout here otherwise you can't break gracefully on Windoze
        try:
            if self.bcserver:
                daemon.requestLoop(lambda s=self: not s.bcserver.shutdown,
                    self.bcserver.preferredTimeOut, [self.bcserver], self.bcserver.bcCallback)
            else:
                daemon.requestLoop()
        except KeyboardInterrupt:
            log.warn("shutdown on user break signal")
            self.shutdown(ns)
        except:
            log.warn("Unexpected exception", exc_info=True)

        log.info("Name Server Shut down gracefully.")

    def handleRequests(self, timeout=None):
        # this method must be called from a custom event loop
        if self.bcserver:
            self.daemon.handleRequests(timeout, [self.bcserver], self.bcserver.bcCallback)
        else:
            self.daemon.handleRequests(timeout)
#
#    def shutdown(self, ns=None):
#        if ns:
#            # internal shutdown call with specified NS object
#            daemon=ns.getDaemon()
#        else:
#            # custom shutdown call w/o specified NS object, use stored instance
#            daemon=self.daemon
#            ns=daemon.getNameServer()
#            del self.daemon
#        daemon.disconnect(ns) # clean up nicely
#        if self.bcserver:
#            self.bcserver.shutdown=True
#        daemon.shutdown()
    
    def stop(self):
        log.info('Shutting down nameserver...')
        daemon = self.daemon
        ns = daemon.getNameServer()
        del self.daemon
        daemon.disconnect(ns)
        if self.bcserver:
            log.info('Stopping bcserver...')
            self.bcserver.shutdown=True
        daemon.shutdown()
        log.info('Daemon shutdown')
