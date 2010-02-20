
from chimera.core.location   import Location
from chimera.core.exceptions import ChimeraException
from chimera.core.constants  import (SYSTEM_CONFIG_DEFAULT_FILENAME,
                                     MANAGER_DEFAULT_HOST, MANAGER_DEFAULT_PORT)

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
    Instrmuments/Controllers names. And for each key, the value can be
    either another map or a sequence of maps.

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

    Chimera accepts definition of instruments and controllers. Besides
    this, there are specials shortcut to most common object types
    (like telescopes).

    For each object, Chimera accepts a set os parameters plus any
    other parameter specific to the given object type. The deault
    parameters are:

    name: a_valid_chimera_name_for_the_instance
    type: ChimeraObject type
    host: where this object is/or will be located.
    port: port where to find the object on the given host

    For special shortcuts the type would be guessed, so the folling
    two entries are equivalent:

    instrument:
     type: Telescope
     name: meade
     device: /dev/ttyS0

    telescope:
     name: meade
     device: /dev/ttyS0
    """

    @staticmethod
    def fromString (string):
        s = SystemConfig()
        s.add(string)
        return s

    @staticmethod
    def fromFile (filename):
        s = SystemConfig()
        s.add(open(filename, "r").read())
        return s

    @staticmethod
    def fromDefault ():
        return SystemConfig.fromFile(SYSTEM_CONFIG_DEFAULT_FILENAME)


    def __init__ (self):

        # primitives
        self.chimera = {}

        self.sites = []
        self.instruments = []
        self.controllers = []

        # specials
        self._specials = ["telescope",
                          "camera",
                          "filterwheel",
                          "dome",
                          "focuser"]

        self._instrumentsSections = self._specials + ["instrument"]
        self._controllersSections = ["controller"]
        self._sections = self._instrumentsSections + self._controllersSections + ["site", "chimera"]

        # to create nice numbered names for objects without a name
        self._useCount = {}
        
        self.chimera["host"] = MANAGER_DEFAULT_HOST
        self.chimera["port"] = MANAGER_DEFAULT_PORT

    def add(self, buffer):
        
        try:
            config = yaml.load(buffer)
            if not config: # empty file
                return
        except yaml.YAMLError, e:
            s = None
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                s = "error at line %s column %s" % (mark.line+1, mark.column+1)
            else:
                s = str(e)

            raise SystemConfigSyntaxException(s)


        # scan the buffer to determine section order, which would be
        # used to guarantee instrument initialization order
        sectionsOrder = []
        for token in yaml.scan(buffer):
            # get all ScalarTokens
            if isinstance(token, yaml.ScalarToken):
                # add to order if is a known section and unique to order
                if token.value in self._sections and token.value not in sectionsOrder:
                    sectionsOrder.append(token.value)

        # parse chimera section first, to get host/port or set defaults
        for type, values in config.items():
            if type.lower() == "chimera":
                self.chimera.update(values)
                # BIGGG FIXME: read all files before create Locations,
                # to avoid this hack
                if "host" in values or "port" in values:
                   # host/port changed
                   for l in self.instruments+self.controllers:
                       l._host = values["host"]
                       l._port = values["port"]            
                 
                del config[type]
                break
            
        # ensure host/port setup on chimera
        if "host" not in self.chimera:
            self.chimera["host"] = MANAGER_DEFAULT_HOST
        
        if "port" not in self.chimera:
            self.chimera["port"] = MANAGER_DEFAULT_PORT
        
        objects = {}

        for type, values in config.items():

            key = type.lower()
            objects[key] = []

            if not isinstance(values, list):
                values = [values]

            for instance in values:

                loc = self._parseLocation(key, instance)
                objects[key].append(loc)

        # create instruments list ordered by sectionsOrder list created above
        for section in sectionsOrder:

            if section in self._instrumentsSections:
                self.instruments += objects[section]

            if section in self._controllersSections:
                self.controllers += objects[section]

        # always use a single site from the last added file
        if "site" in objects:
            self.sites = [objects["site"][0]]
        
        return True

    def _getDefaultName(self, type):
        if not type in self._useCount:
            self._useCount[type] = 0

        name = "%s_%d" % (str(type), self._useCount[type])
        self._useCount[type] += 1
        return name
    
    def _parseLocation (self, type, dic):

        name = dic.pop('name', self._getDefaultName(type))

        # replace some invalid chars from object name
        name = name.replace(" ", "_")
        name = name.replace('"', "_")
        name = name.replace("'", "_")

        if type=="site": # keep name
          dic["name"] = name

        cls  = dic.pop('type', None)

        if not cls:
            if type in self._specials or type == "site":
                cls = type.capitalize()
            else:
                raise TypeNotFoundException("%s %s must have a type." % (type,
                                                                         name))
            
        host = dic.pop('host', self.chimera["host"])
        port = dic.pop('port', self.chimera["port"])

        return Location(name=name, cls=cls, host=host, port=port, config=dic)

