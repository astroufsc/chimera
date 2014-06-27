import subprocess
import logging
import snmp_passpersist as spp

from chimera.core.chimeraobject import ChimeraObject


class SnmpMonitor(ChimeraObject):

    """
    SNMP MIB tree for Chimera

    Chimera MIB:

    +--chimera                                         .1.3.6.1.3.53
       |
       +--R--telescopeGroup(1)                         .1.3.6.1.3.53.1
       |     |
       |     +--R--telescopeName(1)                    .1.3.6.1.3.53.1.1
       |     +--R--telescopeModel(2)                   .1.3.6.1.3.53.1.2
       |     +--R--telescopeCommDevice(3)              .1.3.6.1.3.53.1.3
       |     +--R--telescopeOptics(4)                  .1.3.6.1.3.53.1.4
       |     +--R--telescopeAperture(5)                .1.3.6.1.3.53.1.5
       |     +--R--telescopeMount(6)                   .1.3.6.1.3.53.1.6
       |     +--R--telescopeFocalLength(7)             .1.3.6.1.3.53.1.7
       |
       +--R--cameraGroup(2)                            .1.3.6.1.3.53.1.2
       |     |
       |     +--R--cameraDevice(1)                     .1.3.6.1.3.53.1.2.1
       |     +--R--cameraCCD(2)                        .1.3.6.1.3.53.1.2.2
       |     +--R--cameraTempDelta(3)                  .1.3.6.1.3.53.1.2.3
       |     +--R--cameraCCDSaturationLevel(4)         .1.3.6.1.3.53.1.2.4
       |     +--R--cameraModel(5)                      .1.3.6.1.3.53.1.2.5
       |     +--R--cameraCCDModel(6)                   .1.3.6.1.3.53.1.2.6
       |     +--R--cameraTelescopeFocalLength(7)       .1.3.6.1.3.53.1.2.7
       |
       +--R--domeGroup(3)                              .1.3.6.1.3.53.3
       |     |
       |     +--R--domeDevice                          .1.3.6.1.3.53.3.1
       |     +--R--domeTelescope                       .1.3.6.1.3.53.3.2
       |     +--R--domeMode                            .1.3.6.1.3.53.3.3
       |     +--R--domeModel                           .1.3.6.1.3.53.3.4
       |     +--R--domeStyle                           .1.3.6.1.3.53.3.5
       |     +--R--domeParkPosition                    .1.3.6.1.3.53.3.6
       |     +--R--domeParkOnShutdown                  .1.3.6.1.3.53.3.7
       |     +--R--domeCloseOnShutdown                 .1.3.6.1.3.53.3.8
       |     +--R--domeAzResolution                    .1.3.6.1.3.53.3.9
       |     +--R--domeSlewTimeout                     .1.3.6.1.3.53.3.10
       |     +--R--domeAbortTimeout                    .1.3.6.1.3.53.3.11
       |     +--R--domeInitTimeout                     .1.3.6.1.3.53.3.12
       |     +--R--domeOpenTimeout                     .1.3.6.1.3.53.3.13
       |     +--R--domeCloseTimeout                    .1.3.6.1.3.53.3.14
       |
       +--R--filterWheelGroup(4)                       .1.3.6.1.3.53.4
       |     |
       |     +--R--filterWheelDevice                   .1.3.6.1.3.53.4.1
       |     +--R--filterWheelFilterWheelModel         .1.3.6.1.3.53.4.2
       |     +--R--filterWheelFilters                  .1.3.6.1.3.53.4.3
       |
       +--R--focuserGroup(5)                           .1.3.6.1.3.53.5
       |     |
       |     +--R--focuserDevice                       .1.3.6.1.3.53.5.1
       |     +--R--focuserModel                        .1.3.6.1.3.53.5.2
       |     +--R--focuserOpentimeout                  .1.3.6.1.3.53.5.3
       |     +--R--focuserMovetimeout                  .1.3.6.1.3.53.5.4
       |
       +--R--guiderGroup(6)                            .1.3.6.1.3.53.6
       |     |
       |     +--R--guiderTelescope                     .1.3.6.1.3.53.6.1
       |     +--R--guiderCamera                        .1.3.6.1.3.53.6.2
       |     +--R--guiderInstrument                    .1.3.6.1.3.53.6.3
       |     +--R--guiderFilterwheel                   .1.3.6.1.3.53.6.4
       |     +--R--guiderFocuser                       .1.3.6.1.3.53.6.5
       |     +--R--guiderSaveimages                    .1.3.6.1.3.53.6.6
       |     +--R--guiderImagesdir                     .1.3.6.1.3.53.6.7
       |     +--R--guiderExptime                       .1.3.6.1.3.53.6.8
       |     +--R--guiderFilterPos                     .1.3.6.1.3.53.6.9
       |     +--R--guiderMaxWindows                    .1.3.6.1.3.53.6.10
       |     +--R--guiderMaxTrials                     .1.3.6.1.3.53.6.11
       |
       +--R--weatherStationGroup(7)                    .1.3.6.1.3.53.7
             |
             +--R--weatherStationDevice                .1.3.6.1.3.53.7.1
             +--R--weatherStationHumidityUnit          .1.3.6.1.3.53.7.2
             +--R--weatherStationTemperatureUnit       .1.3.6.1.3.53.7.3
             +--R--weatherStationWindUnit              .1.3.6.1.3.53.7.4
             +--R--weatherStationDewPointUnit          .1.3.6.1.3.53.7.5
             +--R--weatherStationPressureUnit          .1.3.6.1.3.53.7.6
             +--R--weatherStationRainUnit              .1.3.6.1.3.53.7.7
             +--R--weatherStationHumidityDelta         .1.3.6.1.3.53.7.8
             +--R--weatherStationTemperatureDelta      .1.3.6.1.3.53.7.9
             +--R--weatherStationWindDelta             .1.3.6.1.3.53.7.10
             +--R--weatherStationDewPointDelta         .1.3.6.1.3.53.7.11
             +--R--weatherStationPressureDelta         .1.3.6.1.3.53.7.12
             +--R--weatherStationRainDelta             .1.3.6.1.3.53.7.13
    """

    def __init__(self):
        """


        """
        ChimeraObject.__init__(self)

    def __start(self):
        # Define the SNMP instance
        try:
            self.ppm = spp.PassPersist('.1.3.6.1.3.53.10')
            logging.info('SNMP monitoring initialized')
        except:
            logging.error('SNMP monitoring uninitialized')
        return

    def populate_mib(self):
        """
        Load all the OIDs that only need loading once
        """
        pass
