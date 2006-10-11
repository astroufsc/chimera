import logging
import time

from uts.core.instrument import Instrument
from uts.interfaces.telescope import TelescopeSlew

class Telescope(Instrument, TelescopeSlew):

	def __init__(self, manager):
            Instrument.__init__(self, manager)
            TelescopeSlew.__init__(self)

        def init(self, config):
		pass
        
        def inst_main(self):
            self.slewComplete("%.10f" % time.time(), "", "")
            time.sleep(1)        
	
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
		#	self.slewComplete(status['position'])
		logging.info("_slewComplete callback")

	def _abortSlew(self, status):
		#self.slewAborted()
		logging.info("_abortSlew callback")
