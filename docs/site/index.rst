.. Chimera documentation master file, created by
   sphinx-quickstart on Fri Sep  5 13:54:04 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

***********************************
Welcome to Chimera's documentation!
***********************************

Introduction
============

:program:`Chimera` was originally thought of as a *Command Line Interface* to
*Observatory Control Systems* in the context of astronomical observation. As such it possesses a very complete and
strong implementation of tools oriented to terminal based interaction. It is also essentially **distributed** in nature,
meaning it can run across computers, operating systems and networks and provide an integrated control system.

In time, **Chimera** has acquired wider functionality, like e.g. graphical user 
interface(s), included support for devices: instruments, cameras, telescopes/domes, 
etc., access to on line catalogs, integration of external tools.

Chimera: Observatory Automation System
======================================

**Chimera** is a package for control of astronomical observatories, aiming at the
creation of remote and even autonomous ("robotic") observatories in a simple manner. 
Using **Chimera** you can easily control telescopes, CCD cameras, focusers and domes 
in a very integrated way.

Chimera is:

**Distributed**
   Fully distributed system. You can use different machines to
   control each instrument and everything will looks like just one.

**Powerful**
   Very powerful autonomous mode. Give a target and exposure parameters
   and Chimera does the rest.

**Hardware friendly**
   Support for most common off-the-shelf components. See `supported devices`_.

**Extensible**
   Very easy to add support for new devices.

**Flexible**
   Chimera can be used in a very integrated mode but also in standalone
   mode to control just one instrument.

**Free**
   It's free (as in *free beer*), licensed under the GNU_  license.

   .. _GNU: https://gnu.org/

**A Python Package**
 	All these qualities are the consequence  of the chosen programming language: Python_.

 	.. _Python: https://www.python.org/

Contents
========

.. toctree::
   :maxdepth: 2

   using
   configuring
   advanced
   chimerafordevs
   supported

Getting Started
===============

Prerequisites
-------------

Your platform of choice will need to have the following software installed:

* Python 2.7; **Chimera** has not been ported to Python3 yet.
* Git;

Installation
------------

Current build status: |build_status|

.. |build_status| image:: https://travis-ci.org/astroufsc/chimera.svg?branch=master
    :target: https://travis-ci.org/astroufsc/chimera

.. _above:

**Chimera** currently lives in Github_. To install it, go to your install directory, and run:

.. _Github: https://github.com/astroufsc/chimera

::

	git clone https://github.com/astroufsc/chimera.git

This will clone the official repository to the working directory. Go to this 
directory; you will find in its content the typical files used in a distutils based 
python install, notably *setup.py*. Your next step is to type:

::

	python setup.py install

Distutils will run, generate eggs, etc., and will install the following python dependencies:

* CherryPy: 3.2.4
* PyYAML: 3.10
* Pyro: 3.16
* RO: 3.3.0
* SQLAlchemy: 0.9.1
* numpy: 1.8.0
* pyephem: 3.7.5.2
* pyfits: : 3.2
* pyserial: 2.7
* pysnmp: 4.2.5
* python-dateutil: 2.2
* python-sbigudrv: 0.5
* pywcs: 1.10.2
* suds: 0.4


Alternative Methods
-------------------

Python virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^^

For those constrained by limited access to their platform, restrictions to the system
provided python or any other reason, the python tool *virtualenv* provides an 
isolated environment in which to install **Chimera**.

* Install virtualenv_;
* Go to your install dir, and run:
  
  ::

  	virtualenv v_name

* This will generate a directory named *v_name*; go in and type
  
  ::

  	source bin/activate

  (See the documentation for details).

* From tyhe same directory, you can now proceed to install as described above_.

.. _virtualenv: https://virtualenv.pypa.io/en/latest/

Virtualization Options
^^^^^^^^^^^^^^^^^^^^^^

We are currently exploring things like Docker_ as options to enable undisturbing
installations; additionally we think it will allow more streamlined support for cross 
platform development.

.. _Docker: https://docker.io/


License
-------

Chimera is Free/Open Software licensed by `GPL v2
<http://www.gnu.org/licenses/gpl.html>`_ or later (at your choice).

