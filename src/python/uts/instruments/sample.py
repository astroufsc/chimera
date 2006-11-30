#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

from uts.core.lifecycle import BasicLifeCycle

class Sample(BasicLifeCycle):

    def __init__(self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init(self, config):
        print "%s config: %s" % (self.manager.getLocation(self).cls, config)

    def control(self):
        pass
