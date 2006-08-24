#! /usr/bin/python
# -*- coding: iso-8859-1 -*-

import glob
import logging

from string import Template
import uts.util.etree.ElementTree as ET

class Driver(object):

    def __init__(self, config):

        self._config = config

        self._name = None
        self._type = None
        self._cmdline = None
       
        self._parameters = {}

        self._pars = {}
        self._defaults = {}

        self._filterSet = {}

        self._parseConfig()

    def __iadd__(self, data):

        if not isinstance(data, dict):
            return self

        for k,v in data.items():

            try:
                # FIXME type checking
                self._pars[k] = v
            except KeyError, e:
                pass

        return self

    def __getitem__(self, item):
        # FIXME type checking and conversion as appopriate
        if item in self._pars:
            return self._pars[item]
        else:
            raise KeyError

    def __setitem__(self, item, value):
        # FIXME type checking
        self._pars[item] = value

    def __contains__(self, item):
        return (item in self._pars)

    def __len__(self):
        return len(self._pars)

    def __iter__(self):
        return iter(self._pars)

    def buildCommand(self, parameters = {}):

        # FIXME: $max on window, filter name to index,
        # bool values, output wildcards

        # try to replace every parameter in parameters,
        # if any parameters rest in blank use default value

        # use last-minute parameters
        self += parameters

        t1 = Template(self._cmdline)

        s1 = t1.safe_substitute(self._pars)

        t2 = Template(s1)
        s2 = t2.safe_substitute(self._defaults)

        return s2

    def help(self):
        
        _str = "%s - %s\n===\n\n" % (self._name, self._type)

        if self._cmdline:
            _str += "cmdline\n===\n\n%s\n\n"  % self._cmdline

        if self._parameters:
            _str += "parameters\n===\n\n"

            for par, value in self._parameters.items():
                _str += "# %s (type: %s, default: %s)\n%s\n\n" % (par,
                                                                  value[0],
                                                                  value[1],
                                                                  value[2])

        if self._filterSet:
            _str += "Filter set\n===\n\n"

            for _filter, _index in self._filterSet.items():
                _str += "%d %s\n" % (_index, _filter)

        return _str[:-1]

    def _parseConfig(self):

        try:

            f = ET.parse(self._config)

        except IOError, e:
            logging.error("Error opening %s (%s)" % (self._config,  repr(e)))
            return False


        driver = f.getroot()
        
        self._type = driver.findtext("type")
        self._name = driver.findtext("name")
        self._cmdline = driver.findtext("cmdline")

        parameters = driver.findall('parameters/parameter')

        for parameter in parameters:
            
            p_name = parameter.findtext("name")
            
            p_type = parameter.findtext("type")

            p_default = parameter.findtext("default")

            p_doc = parameter.findtext("doc")

            # name => [type, default, doc] possible unchanged for the whole life of the driver
            self._parameters[p_name] = [p_type, p_default, p_doc]

            # to speedup some things
            self._pars[p_name] = p_default
            self._defaults[p_name] = p_default


        filters = driver.findall("filterset/filter")

        for _filter in filters:
            f_index = _filter.findtext("index")
            f_name = _filter.findtext("name")

            self._filterSet[f_name] = int(f_index)
               

class NullDriver(object):
    def __init__(self):
        pass
    def help(self):
        return "null driver"

class DriverFactory(object):

    def __init__(self, base = '/etc/uts/drivers/'):
        self.base = base
        pass
    
    def get(self, drv):

        drivers = glob.glob('%s/*%s*.xml' % (self.base, drv))

        if drivers:
            driver = Driver(drivers[0])
            return driver
        else:
            return NullDriver()

if __name__ == '__main__':

    import sys

    if (len (sys.argv) == 3):
        driver = DriverFactory(sys.argv[1]).get(sys.argv[2])
        print driver.help()

#     if (len(sys.argv) > 1):

#         for inst in sys.argv[1:]:
#             d = Driver(inst)
#             d.buildCommand({})
#             print d.help()
#             print
    
    
