#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

_me = "FALSO_CHEFAO"


from uts.core.instrument import Instrument

class FalsoChefao(Instrument):

    def __init__(self):
        Instrument.__init__(self, _me)

        # adiciona quantas secretárias externas forem necessárias
        self.addSec("WEATHER")
        self.notify("WEATHER", "LOW_TEMP", self.lowTemp)
        self.notify("WEATHER", "HIGH_TEMP", self.highTemp)
        
    def lowTemp(self, event, data):
        """
        lowTemp callback: 
        """
        # notifica os interessados que o telescópio chegou ao alvo.
        #       self.status("SLEW_COMPLETE", "Chegou!")
        print event
        print data


    def highTemp(self, event, data):
        """
        highTemp callback: 
        """
        # notifica os interessados que o telescópio chegou ao alvo.
        #       self.status("SLEW_COMPLETE", "Chegou!")
        print event
        print data


if __name__ == '__main__':

    e = FalsoChefao()
    e.main()
    
