#! /usr/bin/python

from distutils.core import setup

setup(name='uts',
      version='0.1',
      description='UTS python wrappers',
      author='P. Henrique Silva',
      author_email='heneique@astro.ufsc.br',
      packages=['uts', 'uts.core', 'uts.controllers', 'uts.interfaces', 'uts.instruments', 'uts.util', 'uts.util.etree'],
      package_data={'uts.core': ['log.config']},
      scripts=['bin/uts']
      )
