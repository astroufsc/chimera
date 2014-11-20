from __future__ import print_function
from blessed import Terminal

from astropy.coordinates import SkyCoord
from astroquery.simbad import Simbad
from astroquery.vizier import Vizier
from astroquery.sdss.core import SDSS

#from chimera.util.position import Position

#from chimera.core.exceptions import ObjectNotFoundException

import logging
logging.getLogger(__name__)


class CatUI():
    """
    If we generalize this UI's use, this class will migrate
    to a suitable place.
    """

    def __init__(self):
        self.t = Terminal()
        print('I\'m running in a {0}x{1} terminal'.format(
            self.t.height, self.t.width))
        #print(self.t.enter_fullscreen)

    def ui_hdr(self):
        """
        Title, catalog in use, ...and fancies
        """
        with self.t.location(0, 0):
            print('{0}{1}'.format(
                self.t.clear, self.t.black_on_white('Chimera Catalog Browser')))
        #print(self.t.height, self.t.width)

    def ui_catname(self, catname):
        """
        Top right info line
        """
        with self.t.location(self.t.width / 2, 0):
            print(self.t.on_red(catname))


class Catalogs():
    """
    Example queries:
    'Landolt', 'Landolt II/183A'
    """
    def __init__(self, catalog):
        self.catalog = catalog

    def run(self):
        # Initiate the curses based user interface machinery...
        print('So far, so good!')
        cui = CatUI()
        cui.ui_hdr()
        cui.ui_catname(self.catalog)
        #cui.ui_catcfg(self.catalog)

    def get_config(self):
        # Display initial values for Vizier queries
        print('Catalog Configuration [{0}]:\n{1}'.format(
            self.catalog, '*' * 21))
        if self.catalog is 'Vizier':
            print('Server:{0}{1}{2}{3}'.format(
                '\t' * 2, Vizier.VIZIER_SERVER, '\n', '-' * 6))
            print('Row Limit:{0}{1}{2}{3}'.format(
                '\t', Vizier.ROW_LIMIT, '\n', '-' * 9))
            print('Query Timeout:{0}{1}{2}{3}'.format(
                '\t', Vizier.TIMEOUT, '\n', '-' * 13))
            print('Cache Location:{0}{1}{2}{3}'.format(
                '\t', Vizier.cache_location, '\n', '-' * 14))
        elif self.catalog is 'Simbad':
            print('Query URL:{0}{1}{2}{3}'.format(
                '\t' * 2, Simbad.SIMBAD_URL, '\n', '-' * 9))
            print('Row Limit:{0}{1}{2}{3}'.format(
                '\t' * 2, Simbad.ROW_LIMIT, '\n', '-' * 9))
            print('Query Timeout:{0}{1}{2}{3}'.format(
                '\t' * 2, Simbad.TIMEOUT, '\n', '-' * 13))
            print('Accepted Wildcards:')
            Simbad.list_wildcards()
        else:
            print('Base URL:\t {0}\n{1}'.format(SDSS.BASE_URL, '-' * 8))
            print('Query URL:\t {0}\n{1}'.format(SDSS.QUERY_URL, '-' * 9))
            print('Maximum Queries: {0}\n{1}'.format(
                SDSS.MAXQUERIES, '-' * 15))

    def get_closest(self, coords):
        """
        Series of specialized queries on the catalog(s), based
        on the UCD1+ keywords.
        :param coords: SkyCoord object
        """

        pass

