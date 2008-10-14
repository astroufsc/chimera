#! /usr/bin/python
# -*- coding: utf-8 -*-

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

from ez_setup import use_setuptools
use_setuptools()

import os
import sys

from setuptools import setup, find_packages

# append chimera to sys.path to get current version
build_dir = os.getcwd ()
src_dir   = os.path.join (build_dir, 'src')

old_sys_path = sys.path
sys.path.insert (0, src_dir)

from chimera.core.version import  _chimera_version_,		\
                                  _chimera_description_,	\
                                  _chimera_long_description_,	\
                                  _chimera_author,		\
                                  _chimera_author_email_,	\
                                  _chimera_license_,		\
                                  _chimera_url_,		\
                                  _chimera_download_url_,	\
                                  _chimera_classifiers_,	\
                                  _chimera_platform_		

# modules

chimera_scripts = ['src/scripts/chimera',
                   'src/scripts/chimera-cam',
                   'src/scripts/chimera-admin',
                   'src/scripts/chimera-tel',
                   'src/scripts/chimera-dome',
                   'src/scripts/chimera-focus',
                   'src/scripts/chimera-console']

# setup

linux_deps = linux_cdeps = []
win32_deps = win32_cdeps = []

# FIXME:
# coords needs an egg to works on Windows, at least without requiring the user to compile TPM
# on Windows, requires numpy 1.0.4 'cause newer version still doesn't have an egg
# and older matplotlib which doesn't require numpy >= 1.1.0

# FIXME: pywcs only works on python 2.5

if sys.platform == "win32":
    win32_cdeps = ["numpy == 1.0.4"]
    win32_deps += ["pywin32 == 210"]
else:
    linux_cdeps = ["numpy >= 1.1.0"]
    linux_deps += ["python-sbigudrv >= 0.1", "coords"]

    if sys.version_info[0:2] >= (2,5):
        linux_deps += ["pywcs"]

setup(name='chimera-python',
      package_dir      = {"": "src"},
      
      packages         = find_packages("src", exclude=["*.tests"]),
      scripts          = chimera_scripts,

      zip_safe         = False,

      # dependencies are installed bottom up, so put important things last
      install_requires = linux_deps + win32_deps + \
                         ["suds == 0.2.4",
                          "CherryPy == 3.0.3",
                          "asciidata == 1.1",
                          "sqlalchemy >= 0.4.5",
                          "Elixir >= 0.5.2",
                          "pyephem > 3.7",
                          "python-dateutil >= 1.4",
                          "RO >= 2.2.7",
                          "pyfits >= 1.3",
                          "pyserial >= 2.2",
                          "Pyro == 3.8.1"] + linux_cdeps + win32_cdeps,

      dependency_links = [
                          "https://fedorahosted.org/suds/attachment/wiki/WikiStart/suds-0.2.4.tar.gz?format=raw",
                          "http://sourceforge.net/project/showfiles.php?group_id=18837&package_id=29259&release_id=630764"
                          "http://www.stsci.edu/resources/software_hardware/pyfits/pyfits-1.3.tar.gz",
                          "http://astropy.scipy.org/svn/astrolib/trunk/coords#egg=coords",
                          "http://astropy.scipy.org/svn/astrolib/trunk/pywcs#egg=pywcs",
                          "http://sourceforge.net/project/showfiles.php?group_id=46487",
                          "http://www.stecf.org/software/PYTHONtools/astroasciidata/asciidata1.1_download.php",
                          ],

      tests_require    = ["nose", "coverage"],

      version          = _chimera_version_,
      description      = _chimera_description_,
      long_description = open("docs/site/index.rst").read(),
      author           = _chimera_author,
      author_email     = _chimera_author_email_,
      license          = _chimera_license_,
      url              = _chimera_url_,
      download_url     = _chimera_download_url_,
      classifiers      = _chimera_classifiers_,
      platforms        = _chimera_platform_)

