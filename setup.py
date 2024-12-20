#!/usr/bin/env python
#!/usr/bin/env python
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.

from setuptools import setup, find_packages

import os

# read version.py file to get version and metadata information
here = os.path.abspath(os.path.dirname(__file__))
version_py = os.path.join(here, "src/chimera/core/version.py")
exec(compile(open(version_py, "rb").read(), version_py, "exec"))

# chimera scripts
chimera_scripts = [
    "src/scripts/chimera",
    "src/scripts/chimera-cam",
    "src/scripts/chimera-admin",
    "src/scripts/chimera-filter",
    "src/scripts/chimera-tel",
    "src/scripts/chimera-dome",
    "src/scripts/chimera-focus",
    "src/scripts/chimera-console",
    "src/scripts/chimera-sched",
    "src/scripts/chimera-weather",
    "src/scripts/chimera-seeing",
]

# platform specific requirements
platform_deps = []

# go!
setup(
    name="chimera-python",
    version=_chimera_version_,  # noqa: F821 (name defined in exec)
    description=_chimera_description_,  # noqa: F821 (name defined in exec)
    long_description=open("docs/site/index.rst").read(),
    url=_chimera_url_,  # noqa: F821 (name defined in exec)
    author=_chimera_author_,  # noqa: F821 (name defined in exec)
    author_email=_chimera_author_email_,  # noqa: F821 (name defined in exec)
    license=_chimera_license_,  # noqa: F821 (name defined in exec)
    package_dir={"": "src"},
    packages=find_packages("src", exclude=["*.tests"]),
    include_package_data=True,
    scripts=chimera_scripts,
    # installation happens in the specified order
    install_requires=[
        "numpy>=1.8.0",
        "pyephem",
        "python-dateutil",
        "PyYAML",
        "RO",
        "suds",
        "SQLAlchemy",
        "redislite",
        "astropy",
    ]
    + platform_deps,
    tests_require=["nose", "coverage", "wheel"],
)
