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
                   'src/scripts/chimera-filter',
                   'src/scripts/chimera-tel',
                   'src/scripts/chimera-dome',
                   'src/scripts/chimera-focus',
                   'src/scripts/chimera-console']

# setup

linux_deps = linux_cdeps = []
win32_deps = win32_cdeps = []

# FIXME: pywcs only works on python 2.5
if sys.platform == "win32":
    win32_cdeps = ["numpy == 1.0.4"]
    win32_deps += ["pywin32 == 210"]
else:

    import pkg_resources
    
    # check if user have Numpy, we don't try to install it, please use your distro default installation
    # method.
    try:
        pkg_resources.require("numpy >= 1.1.0")
    except pkg_resources.DistributionNotFound:
        print >> sys.stderr, "*"*80
        print >> sys.stderr, "You don't seem to have Numpy installed. Please install Numpy >= 1.1.0 and try again."
        print >> sys.stderr, "*"*80
        sys.exit(1)

    linux_deps += ["python-sbigudrv == 0.1", "pyephem == 3.7.3.3"]
    
    if sys.version_info[0:2] >= (2,5):
        linux_deps += ["pywcs"]

setup(name='chimera-python',
      package_dir      = {"": "src"},
      
      packages         = find_packages("src", exclude=["*.tests"]),
      scripts          = chimera_scripts,
      data_files       = [("chimera/core", ["src/chimera/core/chimera.global.config",
                                            "src/chimera/core/chimera.sample.config"])],

      zip_safe         = False,

      # dependencies are installed bottom up, so put important things last
      install_requires = linux_deps + win32_deps + \
                         ["PyYAML == 3.08",
                          "suds == 0.3.4",
                          "asciidata == 1.1",
                          #"SQLAlchemy == 0.4.8",
                          #"Elixir == 0.6.1",
                          "python-dateutil == 1.4.1",
                          "RO == 2.2.8",
                          "pyfits == 1.3",
                          "pyserial == 2.4",
                          "Pyro == 3.8.1"] + linux_cdeps + win32_cdeps,

      dependency_links = [os.path.join(os.path.dirname(__file__), "contrib")],

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

