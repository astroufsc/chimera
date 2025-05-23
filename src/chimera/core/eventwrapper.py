# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.methodwrapper import MethodWrapperDispatcher

__all__ = ["EventWrapperDispatcher"]


class EventWrapperDispatcher(MethodWrapperDispatcher):

    def __init__(self, wrapper, instance, cls):
        MethodWrapperDispatcher.__init__(self, wrapper, instance, cls)

    def call(self, *args, **kwargs):
        self.instance.get_proxy().publish_event(
            f"{self.instance.get_location()}/{self.func.__name__}", args[1:], kwargs
        )

    def __iadd__(self, other):
        self.instance.get_proxy().subscribe_event(
            f"{self.instance.get_location()}/{self.func.__name__}", other
        )

    def __isub__(self, other):
        self.instance.get_proxy().unsubscribe_event(
            f"{self.instance.get_location()}/{self.func.__name__}", other
        )
