#! /usr/bin/python
# -*- coding: iso8859-1 -*-

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

import os
import sys

from distutils.core import setup

# append chimera to sys.path to get current version
build_dir = os.getcwd ()
src_dir   = os.path.join (build_dir, 'src/')

old_sys_path = sys.path
sys.path.insert (0, src_dir)


from chimera.core.version import ( _chimera_version_,
                                   _chimera_description_,
                                   _chimera_long_description_,
                                   _chimera_author,
                                   _chimera_author_email_,
                                   _chimera_license_,
                                   _chimera_url_,
                                   _chimera_download_url_,
                                   _chimera_classifiers_,
                                   _chimera_platform_)

# modules

chimera_modules = ['chimera',
                   'chimera.core',
                   'chimera.controllers',
                   'chimera.drivers',
                   'chimera.drivers.sbig',
                   'chimera.interfaces',
                   'chimera.instruments',
                   'chimera.util',
                   'chimera.util.etree']

chimera_scripts = ['src/scripts/chimera']

chimera_data    = [ ("/etc/chimera", ["src/config/site.xml"]) ]

# setup

setup(name='chimera',
      package_dir      = {"chimera": "src/chimera/"},
      
      packages         = chimera_modules,
      scripts          = chimera_scripts,
      data_files       = chimera_data,
      
      version          = _chimera_version_,
      description      = _chimera_description_,
      long_description = _chimera_long_description_,
      author           = _chimera_author,
      author_email     = _chimera_author_email_,
      license          = _chimera_license_,
      url              = _chimera_url_,
      download_url     = _chimera_download_url_,
      classifiers      = _chimera_classifiers_,
      platforms        = _chimera_platform_)

