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

   pip install git+https://github.com/astroufsc/chimera.git

This will clone the official repository and install into your system. Make sure that you have the right permissions to
do this.

Distutils will install automatically the following Python dependencies:

* astropy
* PyYAML: 3.10
* Pyro: 3.16
* RO: 3.3.0
* SQLAlchemy: 0.9.1
* numpy: 1.8.0
* pyephem: 3.7.5.2
* python-dateutil: 2.2
* suds: 0.4


Alternative Methods
-------------------

Alternatively, you can follow the how-tos below to install it on a virtual enviroment and on Windows.

Windows using `Anaconda`_ Python distribution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These steps were tested with `Anaconda`_ version 2.3.0.

* Download and install the latest `Anaconda`_ version for Windows.

* Download and install git for windows at https://msysgit.github.io/

* Install Visual C++ 9.0 for Python 2.7 (for pyephem package): https://www.microsoft.com/en-us/download/details.aspx?id=44266

* Open the Anaconda Command Prompt and install chimera using pip:
::

   pip install git+https://github.com/wschoenell/chimera.git

* After install, you can run chimera and its scripts by executing
::

   python C:\Anaconda\Scripts\chimera

On the first run, chimera creates a sample configuration file with fake instruments on ``%HOMEPATH%\chimera\chimera.config``

* **Optional:** For a convenient access create a VBS script named ``chimera.vbs`` on Desktop containing:
::

    CreateObject("Wscript.Shell").Run("C:\Anaconda\python.exe C:\Anaconda\Scripts\chimera -vvvvv")

.. _Anaconda: http://continuum.io

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

