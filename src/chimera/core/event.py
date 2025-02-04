# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.constants import EVENT_ATTRIBUTE_NAME

__all__ = ["event"]


def event(method):
    """
    Event annotation.
    """

    setattr(method, EVENT_ATTRIBUTE_NAME, True)
    return method
