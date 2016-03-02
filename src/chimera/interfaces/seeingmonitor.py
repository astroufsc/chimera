from collections import namedtuple
from astropy import units
from chimera.core.interface import Interface


class SeeingValue(namedtuple('SeeingValue', 'time value unit')):
    """
    Named tuple that represents a measure
    """
    pass

class ISeeingMonitor(Interface):
    """
    Interface for seeing monitor measurements.
    """

    __config__ = {"device": None,           # seeing monitor device
                  "model": "unknown",     # seeing monitor model
                  }


    # Accepted units for each function.
    __accepted_seeing_units__ = [
        units.arcsec
    ]

    __accepted_flux_units__ = [
        units.watt / (units.m**2)
    ]

    __accepted_airmass_units__ = [
    units.dimensionless_unscaled
    ]

    def getSeeing(self, unit):
        """
        Returns a Seeing Value named tuple with the current seeing
        """

    def getSeeingAtZenith(self, unit):
        """
        Returns a Seeing Value named tuple with the current seeing corrected for the Zenital position
        """


    def getFlux(self, unit):
        """
        Returns a Seeing Value named tuple with flux of the source been used for measuring seeing
        """

    def getAirmass(self, unit):
        """
        Returns a Seeing Value named tuple with the air mass of the source used for measuring seeing
        """