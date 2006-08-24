#!/usr/bin/env python

import sys
import logging
import commands
import socket

class SpmNet:

    def __init__(self, server = 'localhost', port = 1750):
        self.server = server
        self.port = port
        self.servers = {}
        
        self.proto = {'PM_SERVER'  : '\x00\x01', 'PM_CLIENT'  : '\x00\x02',
					  'PM_CLOSE'   : '\x00\x03', 'PM_RESEND'  : '\x00\x04',
					  'PM_QUIT'    : '\x00\x05', 'PM_SORRY'   : '\x00\x06',
                      'PM_OK'      : '\x00\x07', 'PM_ACCEPT'  : '\x00\x08',
					  'PM_TABLE'   : '\x00\x09', 'PM_RMSERVER': '\x00\x10',
					  'PM_FWINIT'  : '\x00\x11', 'PM_SHARE'   : '\x00\x12',
                      'PM_OKSHARE' : '\x00\x13', 'PM_BIGBUF'  : 1024,
					  'PM_MAXTRY'  : 20 }

        self.getServers()

    def getPort(self, server = None):
        """
        Retorna a porta de um dado servidor.
        @param server servidor do qual deseja saber a porta
        """

        try:
            return self.servers[server]
        except KeyError:
            return 0
                
    def getServers(self):
        """
        Retorna um dictionary com os servidores e respectivas portas
        ativos no momento.
        """

        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            sk.connect((self.server, self.port))
            sk.send(self.proto['PM_TABLE'])
                
            if sk.recv(2) == self.proto['PM_OK']:
                num = sk.recv(2)

                data = sk.recv(self.proto['PM_BIGBUF'])
                data = data.split('\x00')
                del data[-1]

                for i in data:
                    item = i.split(':')
                    self.servers[item[0].strip()] = int(item[1])

                sk.close()

                return self.servers

            elif sk.recv(2) == self.proto['PM_RESEND']:
                sk.close()
            
        except socket.error, msg:
            logging.exception("Error %s:" % msg[1])
            sk.close()

    def dumpTable(self):
        for i,v in self.servers.items():
            print "%s %d" % (i, v)


class SpmCommand:

    def __init__(self, server = 'localhost', spmtable = None):
        
        self.server = server
        self.servers = {}

        self.getServers()

    def getPort(self, server = None):
        """
        Retorna a porta de um dado servidor.
        @param server servidor do qual deseja saber a porta
        """

        try:
            return self.servers[server]
        except KeyError:
            return 0
                
    def getServers(self):
        """
        Retorna um dictionary com os servidores e respectivas portas
        ativos no momento.
        """

        try:
            out = commands.getoutput("spmtable")
            out = out.split('\n')[2:-1]

            for i in out:
                self.servers[i.split(':')[1].strip()] = int(i.split(':')[2].strip())

            return self.servers
        except Exception, e:
            logging.exception("Error getting servers.")
            return False

    def dumpTable(self):
        for i,v in self.servers.items():
            print "%s %d" % (i, v)

Spm = SpmCommand

#--
if __name__ == '__main__':

    if(len(sys.argv) < 2):
        spm = Spm()
    else:
        spm = Spm(sys.argv[1])

    spm.dumpTable()

