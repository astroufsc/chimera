import os
import time

from astropy.io import ascii

from chimera.util.coord import Coord


class TestCoord:

    @staticmethod
    def equal(a, b, e=0.0001):
        return abs(a - b) <= e

    def test_parsing_conversion_bsc(self):
        """Parsing and comparing to Vizier calculated values the entire 5th Bright Star Catalogue"""

        bsc = ascii.read(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "bsc.dat")),
            format="tab",
            converters={},
        )

        expected_ra = []
        expected_ra_str = []

        expected_dec = []
        expected_dec_str = []

        ra = []
        dec = []

        for row in bsc:
            expected_ra.append(row[0])
            expected_dec.append(row[1])

            expected_ra_str.append(row[2].strip())
            expected_dec_str.append(row[3].strip())

            ra.append(Coord.from_hms(str(row[2])))
            dec.append(Coord.from_dms(str(row[3])))

        for i in range(len(bsc)):
            # use e=0.0001 'cause its the maximum we can get with Vizier data (4 decimal places only)

            # test conversion from HMS DMS to decimal
            assert TestCoord.equal(
                ra[i].deg, expected_ra[i], e=1e-4
            ), f"ra: {expected_ra[i]:.6f} != coord ra: {ra[i].deg:.6f} ({expected_ra[i] - ra[i].deg:.6f})"

            assert TestCoord.equal(
                dec[i].deg, expected_dec[i], e=1e-4
            ), f"dec: {expected_dec[i]:.6f} != coord dec: {dec[i].deg:.64f} ({expected_dec[i] - dec[i].deg:.6f})"

            # test strfcoord implementation
            assert expected_ra_str[i] == ra[i].strfcoord(
                "%(h)02d %(m)02d %(s)04.1f"
            ), "ra: {} != coord ra: {}".format(
                expected_ra_str[i],
                ra[i].strfcoord("%(h)02d %(m)02d %(s)04.1f"),
            )

            assert expected_dec_str[i] == dec[i].strfcoord(
                "%(d)02d %(m)02d %(s)02.0f"
            ), "dec: {} != coord dec: {}".format(
                expected_dec_str[i],
                dec[i].strfcoord("%(d)02d %(m)02d %(s)02.0f"),
            )

    def test_parsing_conversion_hipparcos(self):
        """Parsing and comparing a subset of the Hipparcos and Tycho Catalog"""

        hipp = ascii.read(
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "hipparcos-tycho.dat")
            ),
            format="tab",
        )

        expected_ra = []
        expected_ra_str = []

        expected_dec = []
        expected_dec_str = []

        ra = []
        ra_hms = []

        dec = []
        dec_dms = []

        for row in hipp:
            expected_ra_str.append(row[0].strip())
            expected_dec_str.append(row[1].strip())

            expected_ra.append(float(row[2]))
            expected_dec.append(float(row[3]))

            ra.append(Coord.from_d(str(row[2])))
            dec.append(Coord.from_d(str(row[3])))

            ra_hms.append(Coord.from_hms(str(row[0])))
            dec_dms.append(Coord.from_dms(str(row[1])))

        for i in range(len(hipp)):
            assert expected_ra_str[i] == ra_hms[i].strfcoord(
                "%(h)02d %(m)02d %(s)05.2f"
            ), "ra: {} != coord ra: {}".format(
                expected_ra_str[i],
                ra_hms[i].strfcoord("%(h)02d %(m)02d %(s)05.2f"),
            )

            assert expected_dec_str[i] == dec_dms[i].strfcoord(
                "%(d)02d %(m)02d %(s)04.1f"
            ), "dec: {} != coord dec: {}".format(
                expected_dec_str[i],
                dec_dms[i].strfcoord("%(d)02d %(m)02d %(s)04.1f"),
            )

            # test conversion from D to D
            assert TestCoord.equal(
                ra[i].deg, expected_ra[i], e=1e-8
            ), f"ra: {expected_ra[i]:.6f} != coord ra: {ra[i].deg:.6f} ({expected_ra[i] - ra[i].deg:.6f})"

            assert TestCoord.equal(
                dec[i].deg, expected_dec[i], e=1e-8
            ), f"dec: {expected_dec[i]:.6f} != coord dec: {dec[i].deg:.64f} ({expected_dec[i] - dec[i].deg:.6f})"

            # test conversion from DMS HMS to D
            assert TestCoord.equal(
                ra_hms[i].deg, expected_ra[i], e=1e-4
            ), f"ra: {expected_ra[i]:.6f} != coord ra: {ra_hms[i].deg:.6f} ({expected_ra[i] - ra_hms[i].deg:.6f})"

            assert TestCoord.equal(
                dec_dms[i].deg, expected_dec[i], e=1e-4
            ), f"dec: {expected_dec[i]:.6f} != coord dec: {dec_dms[i].deg:.64f} ({expected_dec[i] - dec_dms[i].deg:.6f})"

    def test_parse_dms(self):

        coords = []

        t_parse = 0
        t_check = 0

        for dd in range(-23, 24):
            for mm in range(0, 60):
                for ss in range(0, 60):
                    s = f"{dd:+03d}:{mm:02d}:{ss:06.3f}"

                    t = time.time()
                    c = Coord.from_dms(s)
                    t_parse += time.time() - t

                    coords.append((s, c))

        for coord in coords:
            t = time.time()
            assert coord[0] == str(coord[1]), (coord[0], "!=", str(coord[1]))
            t_check += time.time() - t

        print(
            f"#{len(coords)} coords parsed in {t_parse:.3f}s ({len(coords) / t_parse:.3f}/s) and checked in {t_check:.3f}s ({len(coords) / t_check:.3f}/s) ..."
        )
