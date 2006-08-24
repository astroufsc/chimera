#!/usr/bin/env python

import sys
from socket import *

class Spm:

    def __init__(self, server = 'localhost', port = 1750):
        self.server = server
        self.port = port

        self.proto = {'PM_SERVER'  : '\x00\x01', 'PM_CLIENT' : '\x00\x02', 'PM_CLOSE' : '\x00\x03',
                      'PM_RESEND'  : '\x00\x04', 'PM_QUIT'   : '\x00\x05', 'PM_SORRY' : '\x00\x06',
                      'PM_OK'      : '\x00\x07', 'PM_ACCEPT' : '\x00\x08', 'PM_TABLE' : '\x00\x09',
                      'PM_RMSERVER': '\x00\x10', 'PM_FWINIT' : '\x00\x11', 'PM_SHARE' : '\x00\x12',
                      'PM_OKSHARE' : '\x00\x13', 'PM_BIGBUF' : 1024, 'PM_MAXTRY' : 20 }

    def getPort(self, server = None):
        """
        Retorna a porta de um dado servidor.
        @param server servidor do qual deseja saber a porta
        """

        pass

    def getTable(self):
        """
        Retorna um dictionary com os servidores e respectivas portas
        ativos no momento.
        """

        dic = {}

        sk = socket(AF_INET, SOCK_STREAM)

        try:
            sk.connect((self.server, self.port))
            sk.send(self.proto['PM_TABLE'])
                
            if sk.recv(2) == self.proto['PM_OK']:
                num = sk.recv(2)
                data = sk.recv(self.proto['PM_BIGBUF'])
                sk.close()

                data = data.split('\x00')
                del data[-1]

                for i in data:
                    item = i.split(':')
                    dic[item[0].strip()] = int(item[1])

                return dic

            elif sk.recv(2) == self.proto['PM_RESEND']:
                sk.close()
                return dic
            
        except error, msg:
            print "Erro:",msg[1]
            sys.exit(-1)

    def dumpTable(self, table=None):
        if table == None:
            table = self.getTable()

            if(table):
                for i,v in table.items():
                    print "%s %d" % (i, v)


if __name__ == '__main__':

    if(len(sys.argv) < 2):
        spm = Spm()
    else:
        spm = Spm(sys.argv[1])

    spm.dumpTable()
