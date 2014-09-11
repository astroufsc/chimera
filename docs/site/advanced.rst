Chimera Advanced Usage
======================

Chimera Concepts
----------------

These are terms commonly found within the software; they represent concepts that are important to understand in order to fully exploit **Chimera**'s capabilities.

  **Manager:**
  	This is the python class that provides every other instance with the tools to be able to function within :program:chimera: initialization, life cycle management, distributed networking capabilities.
  **ChimeraObject:**
  	In order to facilitate the administration of objects, the **Manager** functionality among other utilities is encapsulated in a **ChimeraObject** class. *Every object in chimera should subclass this one.* More details are available in :ref:`chimeraobj`.
  **Location:**
  	Every chimera object running somewhere is accessible via a URI style identifier that uniquely *locates* it in the distributed environment; it spells like:
  	[host:port]/ClassName/instance_name[?param1=value1,...].

  	The host:port may be left out if the referred object is running in the *localhost*, and/or have been defined in the configuration file.

.. _Advanced:

Advanced Chimera Configuration
------------------------------

Every **ChimeraObject** has a *class attribute*, a python dictionary that defines possible configuration options for the object, along with sensible defaults for each. This attribute, named :attr:`__config__`, can be referred to when looking for options to include in the *configuration file*. For example, the telescope interface default :attr:`__config__`::

    __config__ = {"device": "/dev/ttyS0",
                  "model": "Fake Telescopes Inc.",
                  "optics": ["Newtonian", "SCT", "RCT"],
                  "mount": "Mount type Inc.",
                  "aperture": 100.0,  # mm
                  "focal_length": 1000.0,  # mm
                  # unit (ex., 0.5 for a half length focal reducer)
                  "focal_reduction": 1.0,
                  }

can have attribute members overwritten and/or added from the configuration file, the others will keep their default values:

	# Meade telescope on serial port

	telescope:

	    driver: Meade [#]_

	    device:/dev/ttyS1 [#]_

.. rubric:: Footnotes

.. [#] added
.. [#] overwritten

Chimera Scripts Advanced Options
--------------------------------

