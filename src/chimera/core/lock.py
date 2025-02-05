# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.constants import LOCK_ATTRIBUTE_NAME

__all__ = ["lock"]


def lock(method):
    """
    Lock annotation.
    """

    setattr(method, LOCK_ATTRIBUTE_NAME, True)
    return method
