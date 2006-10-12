#! /usr/bin/python

from distutils.core import setup

uts_modules = ['uts',
               'uts.core',
               'uts.controllers',
               'uts.drivers',
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

