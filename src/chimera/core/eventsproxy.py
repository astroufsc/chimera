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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from chimera.core.proxy import Proxy

import logging
import chimera.core.log

import Pyro.errors

log = logging.getLogger(__name__)


__all__ = ['EventsProxy']


class EventsProxy:

    def __init__(self):
        self.handlers = {}

    def subscribe (self, handler):

        topic = handler["topic"]

        if topic not in self.handlers:
            self.handlers[topic] = []

        if handler["handler"] not in self.handlers[topic]:
            self.handlers[topic].append(handler["handler"])

        return True

    def unsubscribe (self, handler):

        topic = handler["topic"]

        if not topic in self.handlers:
            return True

        if handler["handler"] not in self.handlers[topic]:
            return True

        self.handlers[topic].remove(handler["handler"])

        return True

    def publish (self, topic, *args, **kwargs):

        if topic not in self.handlers:
            return True

        excluded = []

        for handler in self.handlers[topic]:

            # FIXME: reuse connections? if not, TIME_WAIT sockets start to slow down things
            proxy = Proxy (uri=handler["proxy"])

            try:
                dispatcher = getattr(proxy, handler["method"])
                #proxy._setOneway ([handler["method"]]) should be faster but results say no!
                dispatcher (*args, **kwargs)
            except AttributeError, e:
                log.debug("Invalid proxy method ('%s %s') for '%s' handler." % \
                          (handler["proxy"], handler["method"], topic))
                excluded.append(handler)
                continue
            except Pyro.errors.ProtocolError, e:
                log.debug ("Unreachable handler (%s). Removing from subscribers list." % proxy)
                excluded.append(handler)
                continue
            except Exception, e:
                log.debug ("Handler (%s) raised an exception. Removing from subscribers list." % proxy)
                log.exception(e)
                excluded.append(handler)
                continue


        # remove unreacheable
        for handler in excluded:
            self.handlers[topic].remove(handler)

        return True
