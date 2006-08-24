#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

_me = "EXEMPLO"

_rpc = ["SLEW",
        "STOP",
        "INFO"]

_notify = ["SLEW_COMPLETE"]

import time

from uts.core.instrument import Instrument

class Exemplo(Instrument):

    def __init__(self):
        Instrument.__init__(self, _me)

        # registra os callbacks responsáveis por cada um dos pontos
        # de controle definidos em _rpc (na mesma ordem)
        self.registerRPC([self.slew,
                          self.stop,
                          self.info])

        # adiciona quantas secretárias externas forem necessárias
#         self.addSec("WEATHER")
#         self.addSec("CAFE")

#         self.notify("WEATHER", "HUMID", self.humidChanged)
  
#     def run(self):
#         pass

        
    def slew(self, event, data):
        """
        slew callback: recebe um objeto Notify com informações sobre
                       quem enviou a ordem e uma lista de argumentos.
        """

        # slew ...
        
        # notifica os interessados que o telescópio chegou ao alvo.
        self.status("SLEW_COMPLETE", "Chegou!")
        print event
        print data

        
    def stop(self, event, data):
        print event
        print data

    def info(self, event, data):
        print event
        print data
	time.sleep(1000)

    def inst_main(self):
	print "Running main control function.. waiting.."
	time.sleep(1)

if __name__ == '__main__':

    e = Exemplo()
    e.main()
    
