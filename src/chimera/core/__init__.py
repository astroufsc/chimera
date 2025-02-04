# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


import os.path
import logging
import shutil

from chimera.core.constants import (
    SYSTEM_CONFIG_DIRECTORY,
    SYSTEM_CONFIG_DEFAULT_FILENAME,
    SYSTEM_CONFIG_DEFAULT_SAMPLE,
    SYSTEM_CONFIG_LOG_NAME,
)

logging.getLogger().setLevel(logging.DEBUG)


def init_sysconfig():

    if not os.path.exists(SYSTEM_CONFIG_DIRECTORY):
        try:
            logging.info(
                f"Default configuration directory not found ({SYSTEM_CONFIG_DIRECTORY}). Creating a new one."
            )
            os.mkdir(SYSTEM_CONFIG_DIRECTORY)
        except IOError as e:
            logging.error(
                f"Couldn't create default configuration directory at {SYSTEM_CONFIG_DIRECTORY} ({e})"
            )

    if not os.path.exists(SYSTEM_CONFIG_DEFAULT_FILENAME):
        logging.info(
            f"Default chimera.config not found. Creating a sample at {SYSTEM_CONFIG_DEFAULT_FILENAME}."
        )

        try:
            shutil.copyfile(
                SYSTEM_CONFIG_DEFAULT_SAMPLE, SYSTEM_CONFIG_DEFAULT_FILENAME
            )
        except IOError as e:
            logging.error(
                f"Couldn't create default chimera.config at {SYSTEM_CONFIG_DEFAULT_FILENAME} ({e})"
            )

    if not os.path.exists(SYSTEM_CONFIG_LOG_NAME):
        try:
            open(SYSTEM_CONFIG_LOG_NAME, "w").close()
        except IOError as e:
            logging.error(
                f"Couldn't create initial log file {SYSTEM_CONFIG_LOG_NAME} ({e})"
            )


init_sysconfig()
