import logging
import time

from uts.core.lifecycle import BasicLifeCycle

from uts.interfaces.telescope import ITelescopeSlew

class Telescope(BasicLifeCycle, ITelescopeSlew):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

        #self.timeslice = 0.05 # 20 Hz
            
    def init(self, config):
        pass

    def shutdown(self):
        pass
        
    def inst_main(self):
        self.slewComplete("%.10f" % time.time(), "", "")
    
    def slew(self, coord):
        # parse and validate coord
        res = self.driver.slewToRaDec.begin((coord['ra'], coord['dec']), callback=self._slewComplete)
        return res.end()

    def isSlewing(self):
        res = self.driver.isSlewing.begin()
        return res.end()

    def abortSlew(self):
        res = self.driver.abortSlew.begin(callback=self._abortSlew)
        return res.end()

    def getRa(self):
        res = self.driver.getRa()
        return res

    def getDec(self):
        return 1000        

    def _slewComplete(self, status):
        # check status
        #if status = True:
        #   self.slewComplete(status['position'])
        logging.info("_slewComplete callback")

    def _abortSlew(self, status):
        #self.slewAborted()
        logging.info("_abortSlew callback")
