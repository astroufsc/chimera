.. Chimera documentation master file, created by
   sphinx-quickstart on Fri Sep  5 13:54:04 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

***********************************
Welcome to Chimera's documentation!
***********************************

..  Introduction
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
   Support for most common off-the-shelf components. See `plugins`_ page for supported devices.

**Extensible**
   Very easy to add support for new devices. See `plugins`_ page for more information.

    .. _plugins: plugins.html

**Flexible**
   Chimera can be used in a very integrated mode but also in standalone
   mode to control just one instrument.

**Free**
   It's free (as in *free beer*), licensed under the GNU_  license.

   .. _GNU: https://gnu.org/

**A Python Package**
    All these qualities are the consequence  of the chosen programming language: Python_.

    .. _Python: https://www.python.org/

.. toctree::
   :hidden:
   :maxdepth: 2

   gettingstarted
   using
   configuring
   plugins
   advanced
   chimerafordevs

Contact us
----------

If you need help on setting chimera on your observatory, please contact us over our `mailing list`_.

Bugs and feature requests can be sent over our `GitHub page`_.

.. _mailing list: https://groups.google.com/forum/#!forum/chimera-discuss
.. _GitHub page: https://github.com/astroufsc/chimera/

Citing chimera
--------------

Chimera OCS v1.0 can be cited by the `DOI`_ below.

.. _DOI: https://en.wikipedia.org/wiki/Digital_object_identifier

.. image:: https://zenodo.org/badge/4820416.svg
   :target: https://zenodo.org/badge/latestdoi/4820416

License
-------

Chimera is Free/Open Software licensed by `GPL v2
<http://www.gnu.org/licenses/gpl.html>`_ or later (at your choice).

