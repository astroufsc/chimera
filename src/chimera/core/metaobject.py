# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import threading

from chimera.core.methodwrapper import MethodWrapper, MethodWrapperDispatcher
from chimera.core.eventwrapper import EventWrapperDispatcher
from chimera.core.lockwrapper import LockWrapper, LockWrapperDispatcher

from chimera.core.rwlock import ReadWriteLock

from chimera.core.constants import (
    EVENT_ATTRIBUTE_NAME,
    CONFIG_ATTRIBUTE_NAME,
    LOCK_ATTRIBUTE_NAME,
    EVENTS_ATTRIBUTE_NAME,
    METHODS_ATTRIBUTE_NAME,
    INSTANCE_MONITOR_ATTRIBUTE_NAME,
    RWLOCK_ATTRIBUTE_NAME,
)


__all__ = ["MetaObject"]


class MetaObject(type):

    def __new__(cls, clsname, bases, _dict):

        # join __config__ dicts, class configuration override base classes
        # configs
        config = {}

        for base in bases:
            if CONFIG_ATTRIBUTE_NAME in base.__dict__ and isinstance(
                base.__dict__[CONFIG_ATTRIBUTE_NAME], dict
            ):
                config = dict(config, **base.__dict__[CONFIG_ATTRIBUTE_NAME])

        # update our class with all configs got from bases, if none defined,
        # our config will be equal to the sum from the bases
        _dict[CONFIG_ATTRIBUTE_NAME] = dict(
            config, **_dict.get(CONFIG_ATTRIBUTE_NAME, {})
        )

        # callables and events
        events = []
        methods = []

        for name, obj in _dict.items():

            if hasattr(obj, "__call__") and not name.startswith("_"):

                # events
                if hasattr(obj, EVENT_ATTRIBUTE_NAME):
                    _dict[name] = MethodWrapper(obj, dispatcher=EventWrapperDispatcher)
                    events.append(name)

                # auto-locked methods
                elif hasattr(obj, LOCK_ATTRIBUTE_NAME):
                    _dict[name] = LockWrapper(obj, dispatcher=LockWrapperDispatcher)
                    methods.append(name)

                # normal objects
                else:
                    _dict[name] = MethodWrapper(obj, dispatcher=MethodWrapperDispatcher)
                    methods.append(name)

        # save our helper atributes to allow better remote reflection (mainly
        # to Console)
        _dict[EVENTS_ATTRIBUTE_NAME] = events
        _dict[METHODS_ATTRIBUTE_NAME] = methods

        # our great Monitors (put here to force use of it)
        _dict[INSTANCE_MONITOR_ATTRIBUTE_NAME] = threading.Condition(threading.RLock())
        _dict[RWLOCK_ATTRIBUTE_NAME] = ReadWriteLock()

        return super(MetaObject, cls).__new__(cls, clsname, bases, _dict)
