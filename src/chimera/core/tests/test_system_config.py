
from chimera.core.systemconfig import SystemConfig, TypeNotFoundException, SystemConfigSyntaxException
from chimera.core.location     import InvalidLocationException
from chimera.core.constants import MANAGER_DEFAULT_HOST, MANAGER_DEFAULT_PORT

from nose.tools import assert_raises

from chimera.core.log import setConsoleLevel
import logging
setConsoleLevel(logging.DEBUG)


class TestSystemConfig (object):

    #
    # test specials
    #

    def test_specials (self):

        s = """
        site:
          name: site1
          type: SiteType
          host: 200.131.64.200
          port: 10000
          config0: value0

        telescope:
          name: tel1
          type: TelescopeType
          host: 200.131.64.201
          port: 10001
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

        system = SystemConfig.fromString(s)

        assert system.sites[0].name == "site1"
        assert system.sites[0].cls  == "SiteType"
        assert system.sites[0].host == "200.131.64.200"
        assert system.sites[0].port == 10000
        assert system.sites[0].config['config0'] == 'value0'

        assert system.instruments[0].name == "tel1"
        assert system.instruments[0].cls  == "TelescopeType"
        assert system.instruments[0].host == "200.131.64.201"
        assert system.instruments[0].port == 10001
        assert system.instruments[0].config['config1'] == 'value1'

        assert system.instruments[1].name == "cam1"
        assert system.instruments[1].cls  == "CameraType"
        assert system.instruments[1].host == "200.131.64.202"
        assert system.instruments[1].port == 10002
        assert system.instruments[1].config['config2'] == 'value2'

        assert system.instruments[2].name == "focuser1"
        assert system.instruments[2].cls  == "FocuserType"
        assert system.instruments[2].host == "200.131.64.203"
        assert system.instruments[2].port == 10003
        assert system.instruments[2].config['config3'] == 'value3'

        assert system.instruments[3].name == "dome1"
        assert system.instruments[3].cls  == "DomeType"
        assert system.instruments[3].host == "200.131.64.204"
        assert system.instruments[3].port == 10004
        assert system.instruments[3].config['config4'] == 'value4'

        assert system.instruments[4].name == "wheel1"
        assert system.instruments[4].cls  == "FilterWheelType"
        assert system.instruments[4].host == "200.131.64.205"
        assert system.instruments[4].port == 10005
        assert system.instruments[4].config['config5'] == 'value5'
        assert system.instruments[4].config['filters'] == ["R", "G", "B", "RGB", "CLEAR"]
        
        assert len(system.instruments) == 5        

    def test_auto_type_name (self):

        s = """
        site:
          name: site1
          #type: SiteType # type would be Site (key.capitalize())
          host: 200.131.64.200
          port: 10000
          config0: value0
        """

        system = SystemConfig.fromString(s)
        assert system.sites[0].name == "site1"
        assert system.sites[0].cls  == "Site"
        assert system.sites[0].host == "200.131.64.200"
        assert system.sites[0].port == 10000
        assert system.sites[0].config['config0'] == 'value0'

    def test_auto_host_port (self):

        s = """
        site:
          name: site1
          #host: 200.131.64.200 # default=None
          #port: 10000 # default=None
        """

        system = SystemConfig.fromString(s)
        assert system.sites[0].host == MANAGER_DEFAULT_HOST
        assert system.sites[0].port == MANAGER_DEFAULT_PORT

    def test_errors (self):
        
        s = """
        telescope:
           type: $lahlah
           name: tel1
        """
        # class cannot have $
        assert_raises(InvalidLocationException, SystemConfig.fromString, s)

        s = """
        telescope
           name: 0
        """
        # syntax eror on first line (forgot ':' after telescope)
        assert_raises(SystemConfigSyntaxException, SystemConfig.fromString, s)

    #
    # instrument primitive
    #
    def test_instrument (self):

        s = """
        instrument:
         name: simple
         type: InstrumentType
        """

        system = SystemConfig.fromString(s)

        assert system.instruments[0].name == 'simple'
        assert system.instruments[0].cls   == 'InstrumentType'

    def test_multiple_instruments (self):
        s = """
        instrument:
         - name: simple
           type: InstrumentType

         - name: simple
           type: InstrumentType
        """

        system = SystemConfig.fromString(s)
        assert len(system.instruments) == 2

    def test_instrument_error (self):
        s = """
        instrument:
         name: simple
         #type: InstrumentType
        """
        assert_raises(TypeNotFoundException, SystemConfig.fromString, s)

    #
    # controller primitive
    #
    def test_controller (self):

        s = """
        controller:
         name: simple
         type: ControllerType
        """

        system = SystemConfig.fromString(s)

        assert system.controllers[0].name == 'simple'
        assert system.controllers[0].cls   == 'ControllerType'

    def test_multiple_controllers (self):
        s = """
        controller:
         - name: simple
           type: ControllerType

         - name: simple
           type: ControllerType
        """

        system = SystemConfig.fromString(s)
        assert len(system.controllers) == 2

    def test_controller_error (self):
        s = """
        controller:
         name: simple
         #type: ControllerType
        """
        assert_raises(TypeNotFoundException, SystemConfig.fromString, s)


        
