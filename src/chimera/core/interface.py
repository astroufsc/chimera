# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.metaobject import MetaObject

__all__ = ["Interface"]


class Interface(object, metaclass=MetaObject):
    pass
