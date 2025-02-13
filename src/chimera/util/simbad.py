# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

# from astroquery.simbad import Simbad as _SimbadClient

from chimera.core.exceptions import ObjectNotFoundException
from chimera.util.position import Position
from chimera.util.coord import Coord


class Simbad(object):
    @staticmethod
    def lookup(name: str) -> Position:
        result = _SimbadClient.query_object(name)
        if result is None or len(result) == 0:
            raise ObjectNotFoundException(f"Couldn't find {name} on SIMBAD")

        return Position(
            coords=(Coord.fromD(result[0]["ra"]), Coord.fromD(result[0]["dec"]))
        )


if __name__ == "__main__":
    s = Simbad()

    while True:
        try:
            obj = input("Give me an object name: ")
            if obj:
                o = s.lookup(obj)
                if not o:
                    continue
                print(o.ra, o.dec)
        except (KeyboardInterrupt, EOFError):
            print()
            break
