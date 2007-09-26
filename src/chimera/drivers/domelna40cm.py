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

import time
import serial
import signal
import threading
import logging
import math
import sys

from chimera.core.lifecycle import BasicLifeCycle
from chimera.interfaces.dome import IDomeDriver

class DomeLNA40cm (BasicLifeCycle, IDomeDriver):

    def __init__(self, manager):

        BasicLifeCycle.__init__ (self, manager)

        self.tty = None
        self.abort = threading.Event ()
        self.slewing = False

        self._errorNo = 0
        self._errorString = ""

        self.timeslice = 0.1

    # -- IBasicLifeCycle implementation --
    
    def init (self, config):

        self.config += config

        if not self.open ():
            return False

        return True

    def shutdown (self):

        if not self.close ():
            return False

        return True

    #def control (self):
    #    logging.info (self.getAz())

    # -- IDomeDriver implementation
        
    def _checkDome (self):

        #tmp = self.tty.timeout
        #self.tty.timeout = 10

        # PH: isto deve ser um ciclo de perguntas tipo: estas acordado?
        # temos que comecar perguntando para a cupula qual seu azimute
        # se vem resposta sinal que estah acordada, certo?
        name = self.getAz()
        # serial tem timeout embutido
        # se der merda retorna False

        # _readline, _write, _read tem que buscar do meade.py
        # o instrumento nao deve chamar coisas que comecao com _
        # soh deveriam ser usados aqui dentro
        # _ eh equivalente ao protected no C++

        if not name and self.getError():
            self.setError (-1, "No response from dome")
            return False

        return True

    def _checkQuirk (self):
        # clear uC command buffer sending and \r, this makes the uC happy!
        self._write("")

        inv = self._readline ()
        if inv != "INVALIDO":
            self.setError (-1, "Quirk error!!!")
            return False

        return True

    def open(self):

        self.device = self.config.device

        self.tty = serial.Serial(self.config.device,
                                 baudrate=9600,         #baudrate
                                 bytesize=serial.EIGHTBITS,    #number of databits
                                 parity=serial.PARITY_NONE,    #enable parity checking
                                 stopbits=serial.STOPBITS_ONE, #number of stopbits
                                 timeout=None,             #set a timeout value, None for waiting forever
                                 xonxoff=0,             #enable software flow control
                                 rtscts=0,              #enable RTS/CTS flow control
                          )

        try:
            self.tty.open()
            self.tty.flushInput ()
            self.tty.flushOutput ()

            # FIXME: better ping test
            if not self._checkDome():
                logging.warning ("Dome is not responding at%s." %  self.config.device)
                return False

            return True

        except serial.SerialException, e:
            self.setError (-1, str(e))
            logging.debug ("Error while opening %s. Exception follows..." % self.config.device)
            logging.exception ()
            return False
            
        except IOError,e:
            self.setError(e)
            logging.debug ("Error while opening %s. Exception follows..." % self.config.device)
            logging.exception ()
            return False

    # disconnect - ***
    def close(self):
        if self.tty.isOpen():
            self.tty.close()
            return True
        else:
            self.setError(-1, "Device not open")
            return False

    def slewToAz(self, az):

        self._checkQuirk ()
            
        dome_az = int (math.ceil (az / self.config.az_res))

        pstn = "CUPULA=%03d" % dome_az

        self.tty.setTimeout (self.config.slew_timeout)

        logging.debug (" slew sent %s" % pstn)
        sys.stdout.flush ()
        self._write(pstn)
        
        ack = self._readline ()
        logging.debug (" slew ack: %s" % ack)
        sys.stdout.flush ()
        
        if ack == "INVALIDO":
            self.setError (-1, "Error trying to slew the dome to azimuth '%s' (dome azimuth '%s')." % (az, dome_az))
            return False

        # ok, we are slewing now
        self.slewing = True

        fin = self._readline ()
        logging.debug (" slew fin: %s" % fin)
        sys.stdout.flush ()

        if fin == "ALARME":
            logging.warning (-2, "Error while slewing dome. Some barcodes couldn't be read correctly. Restarting the dome and trying again.")
            # FIXME: restart the dome and try again
            return False

        if fin.startswith ("CUPULA="):
            self.slewing = False
            time.sleep (0.3) # FIXME: how much sleep we need?
            return True
        else:
            self.setError (-1, "Unknow error while slewing. Received '%s' from dome." % fin)
            self.slewing = False
            return False

    def isSlewing (self):
        return self.slewing

#     def abortSlew(self):
#         if not self.isSlewing ():
#             return False
        
#         self._checkQuirk ()

#         self._write("PARAR")

#         self.tty.setTimeout (self.config.abort_timeout)
#         ack = self._readline ()

#         if ack != "PARADO":
#             self.setError (-1, "Error while trying


    def getAz(self):

        self._checkQuirk ()

        self.tty.setTimeout (10)

        cmd = "POSICAO?"

        logging.debug (" getAz sent %s" % cmd)
        sys.stdout.flush ()
        
        self._write(cmd)
        
        ack = self._readline ()
        logging.debug (" getAz ack %s" % ack)
        sys.stdout.flush ()        

        # check timeout
        if not ack:
            self.setError (-1, "Couldn't get azimuth after %d seconds." % 10)
            return False

        # uC is going crazy
        if ack == "INVALIDO":
            self.setError (-1, "Error getting dome azimuth (ack=INVALIDO).")
            return False

        # get ack return
        if ack.startswith("CUPULA="):
            ack = ack[ack.find("=")+1:]
            
        if ack == "ERRO":
            logging.error ("Dome is in invalid state. Restarting and trying again.")
            # FIXME: restart and try again
            return False

        self.azimuth = int (math.ceil( int(ack) * self.config.az_res) )

        return self.azimuth
    
    def slitOpen (self):

        self._checkQuirk ()

        cmd = "ABRIR"
        
        logging.debug (" slitOpen sent %s" % cmd)
        sys.stdout.flush ()

        self._write(cmd)

        ack = self._readline()
        logging.debug (" slitOpen ack %s" % ack)
        sys.stdout.flush ()        
        
        if ack != "ABRINDO":
            self.setError (-1, "Error trying to open the slit.")
            return False

        self.tty.setTimeout (self.config.open_timeout)

        fin = self._readline ()
        logging.debug (" slitOpen fin %s" % fin)
        sys.stdout.flush ()        

        # check timeout
        if not fin:
            self.setError (-1, "Dome is still opening after %d seconds" % self.config.open_timeout)
            return False

        if fin.startswith ("ABERTO"):
            return True
        else:
            self.setError (-1, "Error opening slit.")
            return False

    def slitClose (self):
        self._checkQuirk ()

        cmd = "FECHAR"

        logging.debug (" slitClose sent %s" % cmd)
        sys.stdout.flush ()

        self._write(cmd)

        ack = self._readline()
        logging.debug (" slitClose ack %s" % ack)
        sys.stdout.flush ()        
        
        if ack != "FECHANDO":
            self.setError (-1, "Error trying to close the slit.")
            return False

        self.tty.setTimeout (self.config.close_timeout)

        fin = self._readline ()
        logging.debug (" slitClose fin %s" % fin)
        sys.stdout.flush ()        

        # check timeout
        if not fin:
            self.setError (-1, "Dome is still closing after %d seconds" % self.config.close_timeout)
            return False

        if fin.startswith ("FECHADO"):
            return True
        else:
            self.setError (-1, "Error closing slit.")
            return False

    # low level
    
    def _read(self, n = 1):
        if not self.tty.isOpen():
            self.setError(-1, "Device not open")
            return ""

        self.tty.flushInput()

        return self.tty.read(n)

    def _readline(self, eol="\n"):
        if not self.tty.isOpen():
            self.setError(-1, "Device not open")
            return ""

        self.tty.flushInput()
        
        ret = self.tty.readline(None, eol)

        if ret:
            # remove eol marks
            return ret[:-3]
        else:
            return ""

    def _readbool(self, n = 1):
        ret = int(self._read(1))

        if not ret:
            return False

        return True

    def _write(self, data, eol="\r"):
        if not self.tty.isOpen():
            self.setError(-1, "Device not open")
            return ""

        self.tty.flushOutput()
        
        return self.tty.write("%s%s" % (data, eol))

    def setError(self, errorNo, errorString):
        self._errorNo = errorNo
        self._errorString = errorString

    def getError(self):
        if self._errorNo:
            ret = (self._errorNo, self._errorString)
        else:
            ret = 0

        self._errorNo = 0
        self._errorString = ""

        return ret

# PH: precisas disto para escrever o driver.
# Algumas coisas que estao acima e que julgamos boas, nao existem
# talvez possamos depois pedir para o Chicao implementa-las
# No início do ano passado havíamos combinado que a princípio seria
# utilizada a porta serial do PC como meio físico de comunicação com o uC
# e que os comandos seriam mensagens ASCII. Pensamos em implantar os
# seguintes comandos:
# 1) CUPULA nnn<CR>, respostas do uC: GIRANDO <CR> no início do
# posicionamento e CUPULA=nnn<CR> ao final do posicionamento. Se durante o
# giro da cúpula, o uC percebesse que alguma etiqueta não foi lida
# corretamente, ele enviaria a mensagem FALHA=nnn<CR> e se a posição de
# destino não fosse alcançada, o uC enviaria a mensagem ERRO=nnn<CR>.
# 2) PARAR<CR>, resposta do uC: PARADO <CR>
# 3) POSICAO?<CR>, resposta do uC: CUPULA=nnn<CR>
# 4) ABRIR<CR> (trapeira), resposta do uC: ABRINDO<CR> e ABERTO<CR>
# 5) FECHAR<CR>, resposta do uC: FECHANDO<CR> e FECHADO<CR>
# Nota: nnn = posição da cúpula em unidades de 2 graus, faixa de valores
# válidos: 0 a 179.
