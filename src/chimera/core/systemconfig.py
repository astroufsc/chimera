# import chimera.core.log
import logging

import yaml

from chimera.core.constants import (
    MANAGER_DEFAULT_HOST,
    MANAGER_DEFAULT_PORT,
    SYSTEM_CONFIG_DEFAULT_FILENAME,
)
from chimera.core.exceptions import ChimeraException
from chimera.core.url import parse_url

log = logging.getLogger(__name__)


class TypeNotFoundException(ChimeraException):
    pass


class SystemConfigSyntaxException(ChimeraException):
    pass


class SystemConfig:
    """

    Chimera configuration system
    ============================

    Chimera uses YAML format for its configuration system. YAML uses
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

    To define more than one instance, just pass a sequence as the
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
    def from_string(string):
        s = SystemConfig()
        s.add(string)
        return s

    @staticmethod
    def from_file(filename):
        s = SystemConfig()
        s.add(open(filename).read())
        return s

    @staticmethod
    def from_default():
        return SystemConfig.from_file(SYSTEM_CONFIG_DEFAULT_FILENAME)

    def __init__(self):
        # primitives
        self.chimera = {}

        self.sites = []
        self.instruments = []
        self.controllers = []

        # specials
        self._specials = [
            "camera",
            "cameras",
            "dome",
            "domes",
            "fan",
            "fans",
            "filterwheel",
            "filterwheels",
            "focuser",
            "focusers",
            "lamp",
            "lamps",
            "telescope",
            "telescopes",
            "seeingmonitor",
            "seeingmonitors",
            "weatherstation",
            "weatherstations",
        ]

        self._instruments_sections = self._specials + ["instrument", "instruments"]
        self._controllers_sections = ["controller", "controllers"]
        self._sections = (
            self._instruments_sections
            + self._controllers_sections
            + ["site", "chimera"]
        )

        # to create nice numbered names for objects without a name
        self._use_count = {}

        self.chimera["host"] = MANAGER_DEFAULT_HOST
        self.chimera["port"] = MANAGER_DEFAULT_PORT

    def add(self, buffer):
        try:
            config = yaml.load(buffer, yaml.Loader)
            if not config:  # empty file
                return
        except yaml.YAMLError as e:
            s = None
            if hasattr(e, "problem_mark"):
                mark = e.problem_mark
                s = f"error at line {mark.line + 1} column {mark.column + 1}"
            else:
                s = str(e)

            raise SystemConfigSyntaxException(s)

        # scan the buffer to determine section order, which would be
        # used to guarantee instrument initialization order
        sections_order = []
        for token in yaml.scan(buffer):
            # get all ScalarTokens
            if isinstance(token, yaml.ScalarToken):
                # add to order if is a known section and unique to order
                if token.value in self._sections and token.value not in sections_order:
                    sections_order.append(token.value)

        # parse chimera section first, to get host/port or set defaults
        for type, values in list(config.items()):
            if type.lower() == "chimera":
                try:
                    if values["host"] == "0.0.0.0":
                        values["host"] = None
                except KeyError:
                    pass
                self.chimera.update(values)
                # BIGGG FIXME: read all files before create Locations,
                # to avoid this hack
                if "host" in values or "port" in values:
                    # host/port changed
                    for loc in self.instruments + self.controllers:
                        loc._host = values["host"]
                        loc._port = values["port"]

                del config[type]
                break

        # ensure host/port setup on chimera
        if "host" not in self.chimera:
            self.chimera["host"] = MANAGER_DEFAULT_HOST

        if "port" not in self.chimera:
            self.chimera["port"] = MANAGER_DEFAULT_PORT

        objects = {}

        for type, values in list(config.items()):
            key = type.lower()
            objects[key] = []

            if not isinstance(values, list):
                values = [values]

            for instance in values:
                url = self._parse_location(key, instance)
                objects[key].append((url, instance))

        # create instruments list ordered by sections_order list created above
        for section in sections_order:
            if section in self._instruments_sections and section in objects:
                self.instruments += objects[section]

            if section in self._controllers_sections and section in objects:
                self.controllers += objects[section]

        # always use a single site from the last added file
        if "site" in objects:
            self.sites = [objects["site"][0]]

        return True

    def _get_default_name(self, type):
        if type not in self._use_count:
            self._use_count[type] = 0

        name = f"{str(type)}_{self._use_count[type]}"
        self._use_count[type] += 1
        return name

    def _parse_location(self, type, dic):
        name = dic.pop("name", self._get_default_name(type))

        # replace some invalid chars from object name
        name = name.replace(" ", "_")
        name = name.replace('"', "_")
        name = name.replace("'", "_")

        if type == "site":  # keep name
            dic["name"] = name

        cls = dic.pop("type", None)

        if not cls:
            if type in self._specials or type == "site":
                cls = type.capitalize()
            else:
                raise TypeNotFoundException(f"{type} {name} must have a type.")

        host = dic.pop("host", self.chimera["host"])
        port = dic.pop("port", self.chimera["port"])

        return parse_url(f"tcp://{host}:{port}/{cls}/{name}")
