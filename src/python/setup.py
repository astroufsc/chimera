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

from distutils.core import setup

uts_modules = ['uts',
               'uts.core',
               'uts.controllers',
               'uts.drivers',
               'uts.drivers.sbig',
               'uts.interfaces',
               'uts.instruments',
               'uts.util',
               'uts.util.etree']

setup(name='uts',
      version='0.1',
      description='UTS python wrappers',
      author='P. Henrique Silva',
      author_email='heneique@astro.ufsc.br',
      packages=uts_modules,
      package_data={'uts.core': ['log.config']},
      scripts=['bin/uts'])

