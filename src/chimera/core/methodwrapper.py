# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import logging

# import chimera.core.log
log = logging.getLogger(__name__)


__all__ = ["MethodWrapper", "MethodWrapperDispatcher"]


class MethodWrapper(object):

    __name__ = ""

    def __init__(self, func, specials=None, dispatcher=None):

        # our wrapped function
        self.func = func

        # will be bounded by the descriptor get
        self.cls = None
        self.instance = None

        self.specials = specials or {}
        self.dispatcher = dispatcher or MethodWrapperDispatcher

        # like a real duck!
        self.__name__ = func.__name__

    # resolver our specials dispatchers
    def __getattr__(self, attr):

        if attr in self.specials:
            return self.specials[attr](self, self.instance, self.cls)

        raise AttributeError()

    # MOST important here: descriptor to bind our dispatcher to an instance
    # and a class
    def __get__(self, instance, cls=None):

        # bind ourselves to pass to our specials
        self.cls = cls
        self.instance = instance

        return self.dispatcher(self, instance, cls)


class MethodWrapperDispatcher(object):

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

    # override this to implement custom behaviour (default just wrap without
    # tricks)
    def call(self, *args, **kwargs):
        return self.func(*args, **kwargs)
