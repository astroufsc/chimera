# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

from chimera.core.location import Location
from chimera.core.exceptions import (
    InvalidLocationException,
    ObjectNotFoundException,
    ChimeraException,
)

import time
import sys
from threading import Thread

from dataclasses import dataclass, field
from typing import Any, Type


@dataclass
class Resource:
    location: Location | None = None
    instance: Any | None = None
    uri: str = ""
    bases: list[Type] = field(default_factory=list)
    created: float = field(default_factory=time.time)
    loop: Thread | None = None


class ResourcesManager:

    def __init__(self):
        self._res = {}

    def add(self, location, instance, loop=None):

        location = self._validLocation(location)

        if location in self:
            raise InvalidLocationException("Location already on the resource pool.")

        entry = Resource()
        entry.location = location
        entry.instance = instance
        if entry.instance is not None:
            entry.bases = [b.__name__ for b in type(entry.instance).mro()]
        entry.loop = loop

        self._res[location] = entry

        # get the number of instances of this specific class, counting this one
        # and not including parents (minus 1 to start counting at 0)
        return len(self.getByClass(location.cls, checkBases=False)) - 1

    def remove(self, location):
        entry = self.get(location)
        del self._res[entry.location]
        return True

    def get(self, item):

        location = self._validLocation(item)

        try:
            index = int(location.name)
            return self._getByIndex(location, index)
        except ValueError:
            # not a numbered instance
            pass

        return self._get(location)

    def getByClass(self, cls, checkBases=True):

        toRet = []

        for k, v in list(self.items()):

            if not checkBases:
                if k.cls == cls:
                    toRet.append(self._res[k])
            else:
                # return if class or any base matches
                if cls == k.cls or cls in v.bases:
                    toRet.append(self._res[k])

        toRet.sort(key=lambda entry: entry.created)
        return toRet

    def _get(self, item):
        location = self._validLocation(item)
        locations = [x.location for x in self.getByClass(location.cls)]

        if location in locations:
            ret = [x for x in list(self.keys()) if x == location]
            return self._res[ret[0]]
        else:
            raise ObjectNotFoundException(f"Couldn't find {location}.")

    def _getByIndex(self, item, index):
        location = self._validLocation(item)
        instances = self.getByClass(location.cls)
        if instances:
            try:
                return self._res[instances[index].location]
            except IndexError:
                raise ObjectNotFoundException(
                    f"Couldn't find {location} instance #{index}."
                )
        else:
            raise ObjectNotFoundException(f"Couldn't find {location}.")

    def _validLocation(self, item):
        ret = item

        if not isinstance(item, Location):
            ret = Location(item)

        return ret

    def __getitem__(self, item):
        try:
            return self.get(item)
        except ChimeraException:
            raise KeyError(f"Couldn't find {item}").with_traceback(sys.exc_info()[2])

    def __contains__(self, item):
        # note that our 'in'/'not in' tests are for keys (locations) and
        # not for values

        item = self._validLocation(item)

        if item in list(self.keys()):
            return True
        else:
            # is this a numbered instance?
            try:
                index = int(item.name)
                return bool(self._getByIndex(item, index))
            except ValueError:
                # not a numbered instance
                return False
            except ObjectNotFoundException:
                # nor a valid object
                return False

    def __iter__(self):
        return iter(self._res)

    def __len__(self):
        return len(self._res)

    def keys(self):
        return list(self._res.keys())

    def values(self):
        return list(self._res.values())

    def items(self):
        return list(self._res.items())

    def iterkeys(self):
        return iter(self._res.keys())

    def iteritems(self):
        return iter(self._res.items())
