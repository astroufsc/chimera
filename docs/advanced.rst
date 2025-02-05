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

Every **ChimeraObject** has a *class attribute*, a python dictionary that defines possible configuration options for
the object, along with sensible defaults for each. This attribute, named :attr:`__config__`, can be referred to when
looking for options to include in the *configuration file*. For example, the telescope interface default
:attr:`__config__`:

.. literalinclude:: ../src/chimera/interfaces/telescope.py
    :lines: 45-57


can have attribute members overwritten and/or added from the plugin and from the configuration file and the others will
keep their default values.

For example, on the meade plugin, besides the default options listed above, we add the configuration option on the
instrument class::

    __config__ = {'azimuth180Correct': True}

and, on the configuration, we can change the defaults to a different value:

::

    # Meade telescope on serial port
    telescope:
        driver: Meade
        device:/dev/ttyS1      # Overwritten from the interface
        my_custom_option: 3.0  # Added on configuration file



Default configuration parameters by interface type
--------------------------------------------------

* **Site**

.. literalinclude:: ../src/chimera/core/site.py
    :lines: 73-78

* Auto-focus

.. literalinclude:: ../src/chimera/interfaces/autofocus.py
    :lines: 40-43

* Autoguider

.. literalinclude:: ../src/chimera/interfaces/autoguider.py
    :lines: 37-46

* Camera

.. literalinclude:: ../src/chimera/interfaces/camera.py
    :lines: 106-117

* Dome

.. literalinclude:: ../src/chimera/interfaces/dome.py
    :lines: 52-72

* Filter wheel

.. literalinclude:: ../src/chimera/interfaces/filterwheel.py
    :lines: 39-43

* Lamp

.. literalinclude:: ../src/chimera/interfaces/lamp.py
    :lines: 39-44

* Focuser

.. literalinclude:: ../src/chimera/interfaces/focuser.py
    :lines: 74-78

* Point Verify

.. literalinclude:: ../src/chimera/interfaces/pointverify.py
    :lines: 29-52

* Telescope

.. literalinclude:: ../src/chimera/interfaces/telescope.py
    :lines: 45-57,65-74,373

* Weather Station

.. literalinclude:: ../src/chimera/interfaces/weatherstation.py
    :lines: 41-43


Fake Instruments default configuration parameters
-------------------------------------------------

* Camera

.. literalinclude:: ../src/chimera/instruments/fakecamera.py
    :lines: 45-47


