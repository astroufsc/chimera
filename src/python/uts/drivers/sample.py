import time
import logging

from uts.core.lifecycle import BasicLifeCycle
	
class Sample(BasicLifeCycle):

        def __init__(self, manager):
                BasicLifeCycle.__init__(self, manager)

	def init(self, config):

		self.config += config

	def dooFoo (self):

		print "tada! doing!!!"
		return True
