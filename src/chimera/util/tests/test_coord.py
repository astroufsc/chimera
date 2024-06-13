
from chimera.util.coord import Coord

from astropy.io import ascii

import os
import time

class TestCoord (object):

    @staticmethod
    def equal (a, b, e=0.0001):
        return ( abs(a-b) <= e)

    def test_parsing_conversion_bsc (self):
        """Parsing and comparing to Vizier calculated values the entire 5th Bright Star Catalogue"""

        bsc = ascii.read(os.path.abspath(os.path.join(os.path.dirname(__file__), 'bsc.dat')), format="tab", converters={})

        expected_ra  = []
        expected_ra_str = []

        expected_dec = []
        expected_dec_str = []

        ra  = []
        dec = []

        for row in bsc:
            expected_ra.append(row[0])
            expected_dec.append(row[1])

            expected_ra_str.append(row[2].strip())
            expected_dec_str.append(row[3].strip())

            ra.append(Coord.fromHMS(str(row[2])))
            dec.append(Coord.fromDMS(str(row[3])))

        for i in range(len(bsc)):
            # use e=0.0001 'cause its the maximum we can get with Vizier data (4 decimal places only)

            # test conversion from HMS DMS to decimal
            assert TestCoord.equal(ra[i].D, expected_ra[i], e=1e-4), \
                "ra: %.6f != coord ra: %.6f (%.6f)" % (expected_ra[i], ra[i].D, expected_ra[i]-ra[i].D)

            assert TestCoord.equal(dec[i].D, expected_dec[i], e=1e-4), \
                "dec: %.6f != coord dec: %.64f (%.6f)" % (expected_dec[i], dec[i].D, expected_dec[i]-dec[i].D)

            # test strfcoord implementation
            assert expected_ra_str[i] == ra[i].strfcoord("%(h)02d %(m)02d %(s)04.1f"), \
                "ra: %s != coord ra: %s" % (expected_ra_str[i], ra[i].strfcoord("%(h)02d %(m)02d %(s)04.1f"))

            assert expected_dec_str[i] == dec[i].strfcoord("%(d)02d %(m)02d %(s)02.0f"), \
                "dec: %s != coord dec: %s" % (expected_dec_str[i], dec[i].strfcoord("%(d)02d %(m)02d %(s)02.0f"))

    def test_parsing_conversion_hipparcos (self):
        """Parsing and comparing a subset of the Hipparcos and Tycho Catalog"""

        hipp = ascii.read(os.path.abspath(os.path.join(os.path.dirname(__file__), 'hipparcos-tycho.dat')), format="tab")

        expected_ra  = []
        expected_ra_str = []

        expected_dec = []
        expected_dec_str = []

        ra  = []
        ra_hms = []

        dec = []
        dec_dms = []

        for row in hipp:
            expected_ra_str.append(row[0].strip())
            expected_dec_str.append(row[1].strip())

            expected_ra.append(float(row[2]))
            expected_dec.append(float(row[3]))

            ra.append(Coord.fromD(str(row[2])))
            dec.append(Coord.fromD(str(row[3])))

            ra_hms.append(Coord.fromHMS(str(row[0])))
            dec_dms.append(Coord.fromDMS(str(row[1])))

        for i in range(len(hipp)):
            assert expected_ra_str[i] == ra_hms[i].strfcoord("%(h)02d %(m)02d %(s)05.2f"), \
                "ra: %s != coord ra: %s" % (expected_ra_str[i], ra_hms[i].strfcoord("%(h)02d %(m)02d %(s)05.2f"))

            assert expected_dec_str[i] == dec_dms[i].strfcoord("%(d)02d %(m)02d %(s)04.1f"), \
                "dec: %s != coord dec: %s" % (expected_dec_str[i], dec_dms[i].strfcoord("%(d)02d %(m)02d %(s)04.1f"))

            # test conversion from D to D
            assert TestCoord.equal(ra[i].D, expected_ra[i], e=1e-8), \
                "ra: %.6f != coord ra: %.6f (%.6f)" % (expected_ra[i], ra[i].D, expected_ra[i]-ra[i].D)

            assert TestCoord.equal(dec[i].D, expected_dec[i], e=1e-8), \
                "dec: %.6f != coord dec: %.64f (%.6f)" % (expected_dec[i], dec[i].D, expected_dec[i]-dec[i].D)

            # test conversion from DMS HMS to D
            assert TestCoord.equal(ra_hms[i].D, expected_ra[i], e=1e-4), \
                "ra: %.6f != coord ra: %.6f (%.6f)" % (expected_ra[i], ra_hms[i].D, expected_ra[i]-ra_hms[i].D)

            assert TestCoord.equal(dec_dms[i].D, expected_dec[i], e=1e-4), \
                "dec: %.6f != coord dec: %.64f (%.6f)" % (expected_dec[i], dec_dms[i].D, expected_dec[i]-dec_dms[i].D)

    def test_parse_dms (self):

        coords = []

        t_parse = 0
        t_check = 0

        for dd in range(-23, 24):
            for mm in range(0, 60):
                for ss in range(0, 60):
                    s = '%+03d:%02d:%06.3f' % (dd,mm,ss)

                    t = time.clock()
                    c = Coord.fromDMS(s)
                    t_parse += time.clock()-t

                    coords.append((s,c))

        for coord in coords:
            t = time.clock()
            assert coord[0] == str(coord[1]), (coord[0], "!=", str(coord[1]))
            t_check += time.clock()-t

        print("#%d coords parsed in %.3fs (%.3f/s) and checked in %.3fs (%.3f/s) ..." % (len(coords), t_parse, len(coords)/t_parse,
                                                                                         t_check, len(coords)/t_check))
