import logging
import time

from uts.core.lifecycle import BasicLifeCycle

class Sample(BasicLifeCycle):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)
            
    def init(self, config):
        pass

    def shutdown(self):
        pass

    def control(self):
        pass

    def slewCompleteCb(self, a, b, c):
        print a

        # instrument
        tel = self.manager.getInstrument("/Telescope/lx200gps")

        if tel:
            print tel.getDec()
            tel.slewComplete += self.slewCompleteCb
        else:
            logging.error("There are no instrument /Telescope/lx200gps avaiable")

        # driver
        driver = self.manager.getDriver("/Meade/meade")

        if driver:
            print driver.getDec()
        else:
            logging.error("There are no driver /Meade/meade avaiable")
