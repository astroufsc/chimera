
from chimera.util.coord import Coord

import asciidata
import os
import gzip

class TestCoord (object):

    @staticmethod
    def equal (a, b, e=0.0001):
        return ( abs(a-b) <= e)

    def test_parsing_conversion_bsc (self):
        """Parsing and comparing to Vizier calculated values the entire 5th Bright Star Catalogue"""

        bsc = asciidata.open(os.path.abspath(os.path.join(os.path.dirname(__file__), 'bsc.dat')), comment_char='#', delimiter='\t')

        expected_ra  = []
        expected_dec = []

        ra  = []
        dec = []

        for i in range(bsc.nrows):
            expected_ra.append(bsc[0][i])
            expected_dec.append(bsc[1][i])
            
            ra.append(Coord.fromHMS(bsc[2][i]))
            dec.append(Coord.fromDMS(bsc[3][i]))

        for i in range(bsc.nrows):
            assert TestCoord.equal(ra[i].D, expected_ra[i]), "ra: %.6f != %.6f (%.6f)" % (ra[i].D, expected_ra[i], expected_ra[i]-ra[i].D)
            assert TestCoord.equal(dec[i].D, expected_dec[i]), "dec: %.6f != %.64f (%.6f)" % (dec[i].D, expected_dec[i], expected_dec[i]-dec[i].D)
