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


import socket

MANAGER_DEFAULT_HOST = socket.gethostname()
MANAGER_DEFAULT_PORT = 7666

MANAGER_LOCATION = '/Manager/manager'

# annotations
EVENT_ATTRIBUTE_NAME  = '__event__'
LOCK_ATTRIBUTE_NAME   = '__lock__'

# special propxies
EVENTS_PROXY_NAME = '__events_proxy__'
CONFIG_PROXY_NAME = '__config_proxy__'

# monitor objects
INSTANCE_MONITOR_ATTRIBUTE_NAME = '__instance_monitor__'
RWLOCK_ATTRIBUTE_NAME           = '__rwlock__'

# reflection
CONFIG_ATTRIBUTE_NAME  = '__config__'
EVENTS_ATTRIBUTE_NAME  = '__events__'
METHODS_ATTRIBUTE_NAME = '__methods__'
