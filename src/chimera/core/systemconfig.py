
from chimera.core.location   import Location
from chimera.core.exceptions import ChimeraException
from chimera.core.constants  import (SYSTEM_CONFIG_DEFAULT_FILENAME,
                                     MANAGER_DEFAULT_HOST, MANAGER_DEFAULT_PORT,
                                     SYSTEM_CONFIG_DEFAULT_GLOBAL)

import yaml

import chimera.core.log
import logging
log = logging.getLogger(__name__)


class TypeNotFoundException (ChimeraException):
    pass


class SystemConfigSyntaxException (ChimeraException):
    pass


class SystemConfig (object):

    """

    Chimera configuration system
    ============================

    Chimera uses YAML format to the configutation system. YAML use
    basic syntax to allow sequences and maps to be easily parsed.

    A map (a key=value sequence) is defined using:
     key: value
     otherkey: value

    will be mapped to {'key': 'value', 'otherkey': 'value'}

    A sequence is defined as (in this case a simple progression)
    - 1
    - 2
    - 3

    will be mapped to [1,2,3]

    Chimera uses both maps and sequences. It use keys that maps to
    Instrmuments/Controllers/Drivers names. And for each key, the
    value can be either another map or a sequence of maps.

    The following example defines a instrument with a few parameters:

     instrument:
      parameter_1: value1
      parameter_2: value2
      parameter_3: value3
                   
    To define more than one instance, just pass an sequence as the
    maps value, as in:

     instrument:
     - parameter_1: value1
       parameter_2: value2
       parameter_3: value3
       
     - parameter_1: other1
       parameter_2: other2
       parameter_3: other3

    You could also pass another map as a parameter value, as in:
    
     instrument:
      parameter_1:
        parameterkey: paramatervalue

    this would be mapped to:

    {'InstrumentType': {'parameter1': {'parameterkey': 'parametervalue'}

    Chimera accepts definition of instruments, controllers and
    drivers. Besides this, there are specials shortcut to most common
    object types (like telescopes).

    For each object, Chimera accepts a set os parameters plus any
    other parameter specific to the given object type. The deault
    parameters are:

    name: a_valid_chimera_name_for_the_instance
    type: ChimeraObject type
    host: where this object is/or will be located.
    port: port where to find the object on the given host
    driver: ChimeraObject of the driver to be used (in instruments only)
    device: device to use for the given driver

    driver could also be an map, which accepts the same parameters as
    normal drivers does (name, type, host, and so on).

    For special shortcuts the type would be guessed, so the folling
    two entries are equivalent:

    instrument:
     type: Telescope
     name: meade
     driver: Meade
     device: /dev/ttyS0

    telescope:
     name: meade
     driver: Meade
     device: /dev/ttyS0
    """

    @staticmethod
    def fromDefault (loadGlobal=True):
        return SystemConfig.fromFile(SYSTEM_CONFIG_DEFAULT_FILENAME, loadGlobal=loadGlobal)

    @staticmethod
    def fromFile (filename, loadGlobal=True):
        s = SystemConfig(open(filename, 'r').read(), loadGlobal=loadGlobal)
        return s

    def __init__ (self, buffer, loadGlobal=True):

        # primitives
        self.chimera = {}
        self.drivers = []
        self.instruments = []
        self.controllers = []

        # specials
        self._specials = ["telescope",
                          "camera",
                          "filterwheel",
                          "dome",
                          "focuser",
                          "site"]
        
        self.telescopes   = []
        self.cameras      = []
        self.filterwheels = []
        self.domes        = []
        self.focusers     = []
        self.sites        = []
        
        if loadGlobal:
            self._loadConfig(open(SYSTEM_CONFIG_DEFAULT_GLOBAL, 'r').read())
            
        self._loadConfig(buffer)

    def _loadConfig (self, buffer):
        
        try:
            config = yaml.load(buffer)
            if not config: # empty file
                return
        except yaml.YAMLError, e:
            s = None
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                s = "Error position: (%s:%s)" % (mark.line+1, mark.column+1)
            else:
                s = str(e)

            raise SystemConfigSyntaxException(s)
        
        # parse chimera section first, to get host/port or set defaults
        for type, values in config.items():
            if type.lower() == "chimera":
                self.chimera.update(values)
                # BIGGG FIXME: read all files before create Locations, to avoid this hack
                if "host" in values or "port" in values:
                   # host/port changed
                   for l in self.drivers+self.instruments+self.controllers:
                       l._host = values["host"]
                       l._port = values["port"]            
                 
                del config[type]
                break
            
        # ensure host/port setup on chimera
        if "host" not in self.chimera:
            self.chimera["host"] = MANAGER_DEFAULT_HOST
        
        if "port" not in self.chimera:
            self.chimera["port"] = MANAGER_DEFAULT_PORT

            
        
        for type, values in config.items():

            key = type.lower()

            if not isinstance(values, list):
                values = [values]

            for instance in values:

                loc = self._parseLocation(key, instance)

                if key == "telescope":
                    self.telescopes.append(loc)
                    self.instruments.append(loc)                    
                elif key == "camera":
                    self.cameras.append(loc)
                    self.instruments.append(loc)                    
                elif key == "filterwheel":
                    self.filterwheels.append(loc)
                    self.instruments.append(loc)                    
                elif key == "dome":
                    self.domes.append(loc)
                    self.instruments.append(loc)                    
                elif key == "focuser":
                    self.focusers.append(loc)
                    self.instruments.append(loc)
                elif key == "site":
                    # just one site allowed
                    self.sites.insert(0, loc)

                elif key == "instrument":
                    self.instruments.append(loc)
                elif key == "controller":
                    self.controllers.append(loc)
                elif key == "driver":
                    self.drivers.append(loc)
                else:
                    self.controllers.append(loc)
                    
        return True
    
    def _parseLocation (self, type, dic):

        name = dic.pop('name', 'noname')
        cls  = dic.pop('type', None)

        if not cls:
            if type in self._specials:
                cls = type.capitalize()
            else:
                raise TypeNotFoundException("%s %s must have a type." % (type, name))
            
        host = dic.pop('host', self.chimera["host"])
        port = dic.pop('port', self.chimera["port"])

        if 'driver' in dic:
            device = dic.pop('device',None)
            driver = self._parseDriver(dic.pop('driver'), device)
            self.drivers.append(driver)
            dic['driver'] = str(driver)

        return Location(name=name, cls=cls, host=host, port=port, config=dic)

    def _parseDriver (self, dic, device):

        if isinstance(dic, dict):
            name = dic.pop('name', 'noname')
            cls  = dic.pop('type', None)

            if not cls:
                raise TypeNotFoundException("Driver '%s' must have a type." % (name))
            
            host = dic.pop('host', self.chimera["host"])
            port = dic.pop('port', self.chimera["port"])

            driver = Location(name=name, cls=cls, host=host, port=port, config=dic)
            
        else:
            driver_name = 'noname'
            driver_cls  = dic
            driver_device = device
            
            driver_config = {}
            
            if driver_device is not None:
                driver_config["device"] = driver_device
            
            driver = Location(name=driver_name,
                              cls=driver_cls,
                              config=driver_config)

        return driver

    def dump (self):

        def printIt (kind, sequence):
            if not sequence: return
            print
            print len(kind)*"="            
            print kind
            print len(kind)*"="

            for item in sequence:
                print "\t", item, item.config


        printIt("Sites", self.sites)
        
        printIt("Controllers", self.controllers)
        printIt("Instruments", self.controllers)        
        printIt("Drivers", self.drivers)

        printIt("Telescopes", self.telescopes)
        printIt("Cameras", self.cameras)
        printIt("FilterWheels", self.cameras)        
        printIt("Focusers", self.focusers)
        printIt("Domes", self.domes)        

