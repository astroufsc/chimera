import logging
import time

from uts.core.controller import Controller

class Sample(Controller):

    def __init__(self, manager):
        Controller.__init__(self, manager)
            
    def init(self):
        pass

    def shutdown(self):
        pass

    def main(self):

        def slewCompleteCb(a, b, c):
            print a

        # instrument
        tel = self.manager.getInstrument("/Telescope/lx200gps")

        if tel:
            print tel.getDec()
            tel.slewComplete += slewCompleteCb
        else:
            logging.error("There are no instrument /Telescope/lx200gps avaiable")

        # driver
        driver = self.manager.getDriver("/Meade/meade")

        if driver:
            print driver.getDec()
        else:
            logging.error("There are no driver /Meade/meade avaiable")
