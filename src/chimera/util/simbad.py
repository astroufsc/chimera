# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.util.position import Position

from xml.etree import ElementTree as ET
from chimera.core.exceptions import ObjectNotFoundException
from xml.parsers.expat import ExpatError

import logging

logging.getLogger("suds").setLevel(1000000000)

from suds.xsd.sxbasic import Import  # noqa: E402

Import.bind("http://schemas.xmlsoap.org/soap/encoding/")

from suds.client import Client  # noqa: E402


class Simbad(object):

    WSDL = "http://cdsws.u-strasbg.fr/axis/services/Sesame?wsdl"

    __cache = {}
    __client = None

    @staticmethod
    def lookup(name):

        if not Simbad.__client:
            Simbad.__client = Client(Simbad.WSDL)

        client = Simbad.__client

        if name in Simbad.__cache:
            return Simbad.__cache[name]

        res = client.service.sesame(name, "x", True)
        target = Simbad._parseSesame(res)

        if not target:
            raise ObjectNotFoundException(f"Couldn't find {name} on SIMBAD")

        Simbad.__cache[name] = target

        return target

    @staticmethod
    def _parseSesame(xml):

        try:
            sesame = ET.fromstring(xml.replace("&", "&amp;"))
            target = sesame.findall("Target")

            if target:
                for resolver in target[0].findall("Resolver"):
                    jpos = resolver.find("jpos")
                    if jpos is None:
                        continue
                    return Position.fromRaDec(*jpos.text.split())
        except ExpatError:
            return False

        return False


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
