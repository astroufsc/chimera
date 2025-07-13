# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import sys
import os

MANAGER_DEFAULT_HOST = "127.0.0.1"
MANAGER_DEFAULT_PORT = 7666

MANAGER_LOCATION = "/Manager/manager"

# annotations
EVENT_ATTRIBUTE_NAME = "__event__"
LOCK_ATTRIBUTE_NAME = "__lock__"

# special propxies
EVENTS_PROXY_NAME = "__events_proxy__"
CONFIG_PROXY_NAME = "__config_proxy__"

# monitor objects
INSTANCE_MONITOR_ATTRIBUTE_NAME = "__instance_monitor__"
RWLOCK_ATTRIBUTE_NAME = "__rwlock__"

# reflection
CONFIG_ATTRIBUTE_NAME = "__config__"
EVENTS_ATTRIBUTE_NAME = "__events__"
METHODS_ATTRIBUTE_NAME = "__methods__"

TRACEBACK_ATTRIBUTE = "__chimera_traceback__"

# system config
if sys.platform == "win32":
    SYSTEM_CONFIG_DIRECTORY = os.path.expanduser("~/chimera")
else:
    SYSTEM_CONFIG_DIRECTORY = os.path.expanduser("~/.chimera")

SYSTEM_CONFIG_DEFAULT_FILENAME = os.path.join(SYSTEM_CONFIG_DIRECTORY, "chimera.config")

if hasattr(sys, "frozen"):
    SYSTEM_CONFIG_DEFAULT_SAMPLE = os.path.join(
        os.path.dirname(sys.executable), "samples", "chimera.sample.config"
    )
else:
    SYSTEM_CONFIG_DEFAULT_SAMPLE = os.path.join(
        os.path.dirname(__file__), "chimera.sample.config"
    )

SYSTEM_CONFIG_LOG_NAME = os.path.join(SYSTEM_CONFIG_DIRECTORY, "chimera.log")

DEFAULT_PROGRAM_DATABASE = os.path.join(SYSTEM_CONFIG_DIRECTORY, "scheduler.db")
