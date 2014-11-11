from __future__ import print_function

from astropysics.obstools import Site
from astropysics.coords.funcs import greenwich_sidereal_time

from chimera.core.chimeraobject import ChimeraObject


class NSite(ChimeraObject):

    """
    .. class Site: Object describing static and dynamic parameters for the
    observatory.
    The default config values reflect the real T80S site at Cerro Tololo,
    according to ..Citation: arXiv:1210.1616v3 [astro-ph.IM].
    Site coordinates can be expressed in several formats:
    TBC
    """
    __config__ = dict(name="T80S",
                      latitude='-30 10 04.31',
                      longitude='-70 48 20.48',
                      altitude=2178,
                      flat_alt=80,
                      flat_az=0
                      )

    def __init__(self):
        ChimeraObject.__init__(self)
        self.site = Site(self['latitude'].replace(' ', ':'),
                         self['longitude'].replace(' ', ':'),
                         alt=self['altitude'])

    def LST(self, apparent=True, returntype='hours'):
        """
        Local Sidereal Time, with default keyword values.
        If apparent=False, the mean LST is returned.
        returntype='hours': decimal value of hour angle
        returntype='string': hh:mm:ss.s formats
        returntype='datetime': a :class:`datetime.time` object
        """
        return self.site.localSiderialTime()

    def GST(self, apparent=True):
        """
        Wrapper for callable
        """
        return greenwich_sidereal_time(self.site.currentobsjd)

    def getMetadata(self, request):
        return [
            ('SITE', self['name'], 'Site name (in config)'),
            ('LATITUDE', str(self['latitude']), 'Site latitude'),
            ('LONGITUD', str(self['longitude']), 'Site longitude'),
            ('ALTITUDE', str(self['altitude']), 'Site altitude'),
        ]
