
from spm import Spm

import sys
import logging
import socket
import select

class PropertyList(dict):

    def __init__(self, config = "/etc/uts/sec/tel.conf"):
        dict.__init__(self)

        self.__config = config
        

    def readConfig(self, config = None):
        if config:
            self.__config = config

        try:
            f = open(self.__config)

            for line in f.readlines():
                
                if ("STATUS" in line) or ("INSTNAME" in line):
                    self[line.split(" ")[1][:-1]] = None

            f.close()

        except Exception, e:
            logging.exception("Error reading sec config %s." % self.__config)


class Notify:

    def __init__(self, sec = "TEL", prop = None, value = None):

        self.sec = sec
        self.prop = prop
        self.value = value

    def __repr__(self):
        return "Event at %s. %s => %s" % (str(self.sec), str(self.prop),
                                          str(self.value))


class Sec:
    """
    Low-level access to UTS Secretary

    UTS Secretary manage instrument properties and register notifies.
    """

    def __init__(self, name, level = "control",
                 server = None,
                 interactive = False,
                 port = None):
        
        """
        @param name: Instrument name (from uts.config)
        @type name: str
        @param level: Access level (control, status)
        @type level: string
        @param server: Server name or IP of Spm (the sockets port Oracle)
        @type server: str
        @param interactive: Verbose mode, default it's False.
        @type interactive: bool
        @param port: not used (future)

        @returns: None
        """
        
        self.name = name
        self.level = level
        self.server = server
        self.port = port
        self.interactive = interactive

        #--
        self.props = PropertyList("/etc/uts/sec/" + self.name.lower() + ".conf")
        self.props.readConfig()

        self.notifies = []
        
        self.sk = None

    def connect(self, server = None, port = None):
        """
        Establish a connection with the Secretary.

        @param server: Server name or IP of Spm (the sockets port Oracle)
        @type server: str
        @param port: not used (future)

        @returns: True on success, False on error.
        """

        if(self.sk):
            self.disconnect()

        self.server = server or 'localhost'

        spm = Spm(self.server)

        self.port = spm.getPort(self.name+self.level)

        if (not self.port):
            self.err("Spm: Cannot get %s port." % (self.name + self.level))
            return False

        try:
            self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sk.connect((self.server, self.port))
            
        except socket.error, msg:
            self.err("Cannot connect to %s (%s)." %
                     (str(self.server) + ":" + str(self.port), msg[1]))
            self.sk = None

            return False

        # OK, connect, here we go!

        # check SERVER_FULL
        full = self.sk.recv(100)
        full = self.removeNULL(full)

        if (full == "SERVER_FULL"):
            self.err("Server full.")
            return False

        # ident
        self.sk.send(self.appendNULL("IDENT INSTRUMENT"))

        ret = self.sk.recv(100)
        ret = self.removeNULL(ret);

        if(ret == "ERROR"):
            self.err("Error trying IDENT INSTRUMENT.")
            return False
        else:
            return True

    def disconnect(self):
        if(self.sk):
            self.sk.send(self.appendNULL("QUIT"))
            self.sk.close()
            self.sk = None

    def appendNULL(self, s):

        return s + "\x00"

    def removeNULL(self, s):

        return s[:-1]

    def out(self, msg, buff = sys.stdout):
        logging.debug(msg)

    def err(self, msg):
        logging.error(msg)

    def setInteractive(self, t = True):
        self.interactive = t

    def status(self, prop, value = None):
        """
        Get or set a property.

        @param prop: The property to get/set.
        @type prop: str
        @param value: The value to set.
        @type value: str
        
        If C{value} not None, set C{prop} to C{value} and return True on success and False on error.
        
        If C{value} equals None (the default), get C{prop} and returns the property value as string or False on error.
        
        If C{self.level} not equals to 'control', return False ('status' secretaries don't have permission to SETSTATUS).
        """

        if(not self.sk):
            self.err("Not connected.")
            return False

        if not (prop in self.props.keys()):
            self.err("%s it's not a valid property." % prop)
            return False

        if (value): # SETSTATUS

            if(self.level != "control"):
                self.err("You dont' have control permission.")
                return False
            
            self.sk.send(self.appendNULL(
                "SETSTATUS " + str(prop) + " " + str(value)))

            res = self.sk.recv(100)
            res = self.removeNULL(res)

            if(res == "OK"):
                self.out("%s ==> %s" % (prop, value))
                return True

            elif(res == "ERROR"):
                self.err("Bad...")
                return False

        else: # GETSTATUS

            # check for notifies
            if(self.level == "status"):
                self.checkNotifies(buffer=True)

            self.sk.send(self.appendNULL("STATUS " + str(prop)))

            res = self.sk.recv(100)
            res = self.removeNULL(res)

            if(res == "ERROR"):
                ret = res
            else:
                ret = res[len("STATUS "):]

            self.out("%s: %s" % (prop, ret))

            return ret

    def isBusy(self):
        ret = self.status(self.name)
    
        if(ret == "OFFLINE") or (ret == "IDLE") or (ret == "DISABLED"):
            return False
        else:
            return True

    def isConnected(self):
        if(self.sk):
            return True
        else:
            return False

    def notify(self, prop):
        """
        Register a notify for C{prop}
 
        @param prop: The property on which you want to be notified
        @type prop: str

        @returns: True on success, False on error.
        @see: L{Sec.unnotify}

        If C{pro} don't exists, C{self.level} equals 'control' or if C{Sec} cannot register the notify return False
        Return True on success.
        
        """

        if(not self.sk):
            self.err("Not connected.")
            return False

        if(not prop in self.props.keys()):
            self.err("Unknow property %s." % prop)
            return False

        if(self.level == "control"):
            self.err("Level must be 'status', not 'control'.")
            return False

        self.checkNotifies(buffer=True)        

        self.sk.send(self.appendNULL("NOTIFY " + str(prop)))

        res = self.sk.recv(100)
        res = self.removeNULL(res)

        if(res == "OK"):
            return True

        elif(res == "ERROR"):
            return False

    def unnotify(self, prop):
        """
        Unregister a notify for C{prop}

        If I{pro} don't exists, I{self.level} equals 'control' or if Sec cannot unregister the notify return False
        
        @returns: True on success, False on error.
        """

        if(not self.sk):
            self.err("Not connected.")
            return False

        if(not prop in self.props.keys()):
            self.err("Unknow property %s." % prop)
            return False

        if(self.level == "control"):
            self.err("Level must be 'status', not 'control'.")
            return False

        self.checkNotifies(buffer=True)        

        self.sk.send(self.appendNULL("UNOTIFY " + str(prop)))

        res = self.sk.recv(100)
        res = self.removeNULL(res)

        if(res == "OK"):
            return True

        elif(res == "ERROR"):
            return False

    def checkNotifies(self, blocking = False, timeout = 60, buffer = False):

        if(not self.sk):
            self.err("Not connected.")
            return False

        if(self.level == "control"):
            self.err("Level must be 'status', not 'control'.")
            return False

        if(blocking):
            wait = select.select([self.sk], [], [], timeout)
        else:
            wait = select.select([self.sk], [], [], 0)

        if(len(wait[0])):
            data = self.sk.recv(255).split('\x00')[:-1]

            res = []
            
            for i in data:
                res.append(Notify(self.name,
								  i.split(" ")[1].strip(),
								  i.split(" ")[2].strip()))
            
            if(buffer):
                self.notifies = self.notifies + res
                return True
            else:
                ret = self.notifies + res
                self.notifies = []

                return ret

        else:

            if (buffer):
                return True

            else:
                ret = self.notifies
                self.notifies = []

                return ret
