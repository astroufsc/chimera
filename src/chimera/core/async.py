# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.methodwrapper import MethodWrapperDispatcher

__all__ = ["BeginDispatcher", "EndDispatcher"]


class BeginDispatcher(MethodWrapperDispatcher):

    def __init__(self, cls, instance, func):
        MethodWrapperDispatcher.__init__(self, cls, instance, func)

    def special(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class EndDispatcher(MethodWrapperDispatcher):

    def __init__(self, cls, instance, func):
        MethodWrapperDispatcher.__init__(self, cls, instance, func)

    def special(self, *args, **kwargs):
        return self.func(*args, **kwargs)
