# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from functools import cache
import urllib.request
import urllib.parse
import json


@cache
def simbad_lookup(object_name) -> tuple[str, float, float, float] | None:
    """
    Perform a SIMBAD lookup for the given object name.

    @param object_name: The name of the object to look up.
    @return: A tuple containing the SIMBAD OID, main ID, RA in hours, and DEC in degrees and epoch 2000.
    @rtype: tuple or None when not found.
    """
    # based on https://gist.github.com/daleghent/2d80fffbaef2f1614962f0ddc04bee92
    url = "https://simbad.u-strasbg.fr/simbad/sim-tap/sync"
    query = f"""
    SELECT basic.OID, main_id, RA, DEC
    FROM basic
    JOIN ident ON oidref = oid
    WHERE id = '{object_name}'
    """
    data = urllib.parse.urlencode(
        {"query": query, "format": "json", "lang": "ADQL", "request": "doQuery"}
    ).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise Exception(f"HTTP Error: {response.status}")
        out = json.load(response)

    if "data" not in out or not out["data"] or len(out["data"]) == 0:
        return None

    main_id = out["data"][0][1]
    ra = out["data"][0][2] / 15.0  # Convert from degrees to hours
    dec = out["data"][0][3]

    return main_id, ra, dec, 2000.0  # epoch 2000


if __name__ == "__main__":
    import time

    while True:
        try:
            obj = input("Give me an object name: ")
            if obj:
                t0 = time.time()
                o = simbad_lookup(obj)
                if not o:
                    print("Object not found, please try again.")
                    continue
                print(o)
                elapsed_time = time.time() - t0
                print(f"Lookup time: {elapsed_time:.2f} seconds")
        except (KeyboardInterrupt, EOFError):
            print()
            break
