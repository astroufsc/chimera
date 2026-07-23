# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>
import logging
from collections.abc import Callable

from chimera.core.constants import (
    CONFIG_ATTRIBUTE_NAME,
    EVENT_ATTRIBUTE_NAME,
    EVENTS_ATTRIBUTE_NAME,
    INSTANCE_MONITOR_ATTRIBUTE_NAME,
    LOCK_ATTRIBUTE_NAME,
    METHODS_ATTRIBUTE_NAME,
)

# import chimera.core.log
log = logging.getLogger(__name__)


__all__ = []


class MethodWrapper:
    def __init__(self, func: Callable[..., None], dispatcher=None):
        # our wrapped function
        self.func = func

        # will be bounded by the descriptor get
        self.cls = None
        self.instance = None

        self.dispatcher = dispatcher or MethodWrapperDispatcher

        # like a real duck!
        self.__name__ = func.__name__

    # MOST important here: descriptor to bind our dispatcher to an instance
    # and a class
    def __get__(self, instance: object, cls: type | None = None):
        # bind ourselves to pass to our specials
        self.cls = cls
        self.instance = instance

        return self.dispatcher(self, instance, cls)


class MethodWrapperDispatcher:
    def __init__(self, wrapper, instance, cls):
        self.wrapper = wrapper
        self.func = wrapper.func
        self.instance = instance
        self.cls = cls

        # go duck, go!
        self.bound_name = f"<bound method {self.cls.__name__}.{self.func.__name__}.begin of {repr(self.instance)}>"

        self.unbound_name = f"<unbound method {self.cls.__name__}.{self.func.__name__}>"

    def __repr__(self):
        if self.instance:
            return self.bound_name
        else:
            return self.unbound_name

    def __eq__(self, other):
        # every attribute access creates a fresh dispatcher: two of them are
        # the same logical callable when they wrap the same function bound to
        # the same instance (what makes `self.event -= self.handler` work)
        if isinstance(other, MethodWrapperDispatcher):
            return self.func is other.func and self.instance is other.instance
        return NotImplemented

    def __hash__(self):
        return hash((id(self.func), id(self.instance)))

    def __call__(self, *args, **kwargs):
        # handle unbound cases (with or without instance as first argument)
        if not self.instance:
            if not args:
                args = [None, None]

            if not isinstance(args[0], self.cls):
                raise TypeError(
                    f"unbound method {self.func.__name__} object must be called with {self.cls.__name__} instance "
                    f"as first argument (got {args[0].__class__.__name__} instance instead)"
                )
            else:
                return self.call(args[0], *args[1:], **kwargs)

        # log.debug("[calling] %s %s" % (self.instance, self.func.__name__))

        return self.call(self.instance, *args, **kwargs)

    # override this to implement custom behaviour (default just wrap without tricks)
    def call(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class EventWrapperDispatcher(MethodWrapperDispatcher):
    def __init__(self, wrapper: MethodWrapper, instance, cls):
        MethodWrapperDispatcher.__init__(self, wrapper, instance, cls)

    def call(self, *args, **kwargs):
        self.instance.__bus__.publish(
            pub=self.instance.get_location(),
            event=self.wrapper.func.__name__,
            args=args[1:],
            kwargs=kwargs,
        )

    def __iadd__(self, other):
        # the object subscribing to its own event: it is both ends
        self.instance.__bus__.subscribe(
            sub=self.instance.get_location(),
            pub=self.instance.get_location(),
            event=self.func.__name__,
            callback=other,
        )
        return self

    def __isub__(self, other):
        self.instance.__bus__.unsubscribe(
            sub=self.instance.get_location(),
            pub=self.instance.get_location(),
            event=self.func.__name__,
            callback=other,
        )
        return self


class LockWrapperDispatcher(MethodWrapperDispatcher):
    def __init__(self, wrapper, instance, cls):
        MethodWrapperDispatcher.__init__(self, wrapper, instance, cls)

    def call(self, *args, **kwargs):
        """
        Locked methods take the object monitor: the bus dispatch layer
        already serializes bus-routed @lock calls per object (FIFO lane),
        but direct in-process calls bypass the bus — the monitor is what
        keeps those mutually exclusive too. The RLock makes nested @lock
        calls on the same thread reentrant.
        """

        lock = getattr(self.instance, INSTANCE_MONITOR_ATTRIBUTE_NAME)

        lock.acquire()

        ret = None

        try:
            ret = self.func(*args, **kwargs)
        finally:
            lock.release()

        return ret


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

                # @lock methods: the marker on the raw function (the
                # wrapper's .func) routes bus requests through a per-object
                # FIFO lane, and the dispatcher takes the instance monitor so
                # direct in-process calls stay mutually exclusive too
                elif hasattr(obj, LOCK_ATTRIBUTE_NAME):
                    _dict[name] = MethodWrapper(obj, dispatcher=LockWrapperDispatcher)
                    methods.append(name)

                # normal objects
                else:
                    # FIXME: there is not a great reason to wrap normal methods, I only did to be consistent
                    #        measure the impact and see if it's worth it
                    _dict[name] = MethodWrapper(obj, dispatcher=MethodWrapperDispatcher)
                    methods.append(name)

        # save our helper atributes to allow better remote reflection (mainly
        # to Console)
        _dict[EVENTS_ATTRIBUTE_NAME] = events
        _dict[METHODS_ATTRIBUTE_NAME] = methods

        # NOTE: the instance monitor and config rwlock are created per
        # instance in ChimeraObject.__init__ — class-level locks made two
        # instances of the same driver block each other

        return super().__new__(cls, clsname, bases, _dict)
