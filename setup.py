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
                   'src/scripts/chimera-tel',
                   'src/scripts/chimera-dome',
                   'src/scripts/chimera-focus',
                   'src/scripts/chimera-console']

# setup

win32_deps = []
if sys.platform == "win32":
    win32_deps = ['pywin32 == 210']
    
setup(name='chimera-python',
      package_dir      = {"": "src"},
      
      packages         = find_packages("src", exclude=["*.tests"]),
      scripts          = chimera_scripts,

      zip_safe         = True,

      install_requires = ["Pyro >= 3.7",
                          "numpy >= 1.0.3",
                          "pyfits >= 1.3",
                          "pyserial >= 2.2",
                          "coords",
                          "python-sbigudrv >= 0.1"] + win32_deps,

      dependency_links = ["http://www.stsci.edu/resources/software_hardware/pyfits/pyfits-1.3.tar.gz",
                          "http://astropy.scipy.org/svn/astrolib/trunk/coords#egg=coords-trunk",
                          "http://sourceforge.net/project/showfiles.php?group_id=46487"],

      tests_require    = ["nose"],
      test_loader      = "nose.loader:TestLoader",
      test_suite       = "src/chimera",
            
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

