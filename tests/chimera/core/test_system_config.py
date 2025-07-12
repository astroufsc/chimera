import logging

import pytest

from chimera.core.constants import MANAGER_DEFAULT_HOST, MANAGER_DEFAULT_PORT
from chimera.core.log import set_console_level
from chimera.core.systemconfig import (
    SystemConfig,
    SystemConfigSyntaxException,
    TypeNotFoundException,
)

set_console_level(logging.DEBUG)


class TestSystemConfig:
    #
    # test specials
    #

    def test_specials(self):
        s = """
        chimera:
            host: 127.0.0.1
            port: 8000
        site:
          name: site1
          type: SiteType
          host: 200.131.64.200
          port: 10000
          config0: value0

        telescope:
          name: tel1
          type: TelescopeType
          config1: value1

        camera:
          name: cam1
          type: CameraType
          host: 200.131.64.202
          port: 10002
          config2: value2

        focuser:
          name: focuser1
          type: FocuserType
          host: 200.131.64.203
          port: 10003
          config3: value3

        dome:
          name: dome1
          type: DomeType
          host: 200.131.64.204
          port: 10004
          config4: value4

        filterwheel:
          name: wheel1
          type: FilterWheelType
          host: 200.131.64.205
          port: 10005
          config5: value5
          filters: [R, G, B, RGB, CLEAR]
        """

        system = SystemConfig.from_string(s)

        assert system.sites[0][0].name == "site1"
        assert system.sites[0][0].cls == "SiteType"
        assert system.sites[0][0].host == "200.131.64.200"
        assert system.sites[0][0].port == 10000
        assert system.sites[0][1]["config0"] == "value0"

        assert system.instruments[0][0].name == "tel1"
        assert system.instruments[0][0].cls == "TelescopeType"
        assert system.instruments[0][0].host == "127.0.0.1"
        assert system.instruments[0][0].port == 8000
        assert system.instruments[0][1]["config1"] == "value1"

        assert system.instruments[1][0].name == "cam1"
        assert system.instruments[1][0].cls == "CameraType"
        assert system.instruments[1][0].host == "200.131.64.202"
        assert system.instruments[1][0].port == 10002
        assert system.instruments[1][1]["config2"] == "value2"

        assert system.instruments[2][0].name == "focuser1"
        assert system.instruments[2][0].cls == "FocuserType"
        assert system.instruments[2][0].host == "200.131.64.203"
        assert system.instruments[2][0].port == 10003
        assert system.instruments[2][1]["config3"] == "value3"

        assert system.instruments[3][0].name == "dome1"
        assert system.instruments[3][0].cls == "DomeType"
        assert system.instruments[3][0].host == "200.131.64.204"
        assert system.instruments[3][0].port == 10004
        assert system.instruments[3][1]["config4"] == "value4"

        assert system.instruments[4][0].name == "wheel1"
        assert system.instruments[4][0].cls == "FilterWheelType"
        assert system.instruments[4][0].host == "200.131.64.205"
        assert system.instruments[4][0].port == 10005
        assert system.instruments[4][1]["config5"] == "value5"
        assert system.instruments[4][1]["filters"] == [
            "R",
            "G",
            "B",
            "RGB",
            "CLEAR",
        ]

        assert len(system.instruments) == 5

    def test_auto_type_name(self):
        s = """
        site:
          name: site1
          #type: SiteType # type would be Site (key.capitalize())
          host: 200.131.64.200
          port: 10000
          config0: value0
        """

        system = SystemConfig.from_string(s)
        assert system.sites[0][0].name == "site1"
        assert system.sites[0][0].cls == "Site"
        assert system.sites[0][0].host == "200.131.64.200"
        assert system.sites[0][0].port == 10000
        assert system.sites[0][1]["config0"] == "value0"

    def test_auto_host_port(self):
        s = """
        site:
          name: site1
          #host: 200.131.64.200 # default=None
          #port: 10000 # default=None
        """

        system = SystemConfig.from_string(s)
        assert system.sites[0][0].host == MANAGER_DEFAULT_HOST
        assert system.sites[0][0].port == MANAGER_DEFAULT_PORT

    def test_errors(self):
        s = """
        telescope:
           type: $lahlah
           name: tel1
        """
        # class cannot have $
        with pytest.raises(ValueError):
            SystemConfig.from_string(s)

        s = """
        telescope
           name: 0
        """
        # syntax eror on first line (forgot ':' after telescope)
        with pytest.raises(SystemConfigSyntaxException):
            SystemConfig.from_string(s)

    #
    # instrument primitive
    #
    def test_instrument(self):
        s = """
        instrument:
         name: simple
         type: InstrumentType
        """

        system = SystemConfig.from_string(s)

        assert system.instruments[0][0].name == "simple"
        assert system.instruments[0][0].cls == "InstrumentType"

    def test_multiple_instruments(self):
        s = """
        instrument:
         - name: simple
           type: InstrumentType

         - name: simple
           type: InstrumentType
        """

        system = SystemConfig.from_string(s)
        assert len(system.instruments) == 2

    def test_instrument_error(self):
        s = """
        instrument:
         name: simple
         #type: InstrumentType
        """
        with pytest.raises(TypeNotFoundException):
            SystemConfig.from_string(s)

    #
    # controller primitive
    #
    def test_controller(self):
        s = """
        controller:
         name: simple
         type: ControllerType
        """

        system = SystemConfig.from_string(s)

        assert system.controllers[0][0].name == "simple"
        assert system.controllers[0][0].cls == "ControllerType"

    def test_multiple_controllers(self):
        s = """
        controller:
         - name: simple
           type: ControllerType

         - name: simple
           type: ControllerType
        """

        system = SystemConfig.from_string(s)
        assert len(system.controllers) == 2

    def test_controller_error(self):
        s = """
        controller:
         name: simple
         #type: ControllerType
        """
        with pytest.raises(TypeNotFoundException):
            SystemConfig.from_string(s)
