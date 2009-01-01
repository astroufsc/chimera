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


import os.path
import logging
import shutil

from chimera.core.constants import (SYSTEM_CONFIG_DIRECTORY,
                                    SYSTEM_CONFIG_DEFAULT_FILENAME,
                                    SYSTEM_CONFIG_DEFAULT_SAMPLE,
                                    SYSTEM_CONFIG_LOG_NAME)

logging.getLogger().setLevel(logging.DEBUG)

def init_sysconfig ():

    if not os.path.exists(SYSTEM_CONFIG_DIRECTORY):
        try:
            logging.info("Default configuration directory not found (%s). Creating a new one." % SYSTEM_CONFIG_DIRECTORY)
            os.mkdir(SYSTEM_CONFIG_DIRECTORY)
        except IOError, e:
            logging.error("Couldn't create default configuration directory at %s (%s)" % (SYSTEM_CONFIG_DIRECTORY, e))

    if not os.path.exists(SYSTEM_CONFIG_DEFAULT_FILENAME):
        logging.info("Default chimera.config not found. Creating a sample at %s." % SYSTEM_CONFIG_DEFAULT_FILENAME)

        try:
            shutil.copyfile(SYSTEM_CONFIG_DEFAULT_SAMPLE, SYSTEM_CONFIG_DEFAULT_FILENAME)
        except IOError, e:
            logging.error("Couldn't create default chimera.config at %s (%s)" % (SYSTEM_CONFIG_DEFAULT_FILENAME, e))

    if not os.path.exists(SYSTEM_CONFIG_LOG_NAME):
        try:
            open(SYSTEM_CONFIG_LOG_NAME, 'w').close()
        except IOError, e:
            logging.error("Couldn't create initial log file %s (%s)" % (SYSTEM_CONFIG_LOG_NAME, e))

init_sysconfig()
