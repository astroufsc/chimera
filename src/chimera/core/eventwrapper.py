#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.


from chimera.core.methodwrapper import MethodWrapperDispatcher

__all__ = ["EventWrapperDispatcher"]


class EventWrapperDispatcher(MethodWrapperDispatcher):

    def __init__(self, wrapper, instance, cls):
        MethodWrapperDispatcher.__init__(self, wrapper, instance, cls)

    def call(self, *args, **kwargs):
        """Publish event."""
        self.instance.getProxy().publish_event(
            f"{self.instance.getLocation()}/{self.func.__name__}", args[1:], kwargs
        )

    def __iadd__(self, other):
        raise NotImplementedError("eventwrapper.py IADD")

    def __isub__(self, other):
        raise NotImplementedError("eventwrapper.py ISUB")
