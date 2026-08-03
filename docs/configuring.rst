Chimera Configuration
=====================

Introduction
------------

For real world use, :program:`chimera` needs to be configured for the subset of devices that comprise the *Observatory* you are driving. This encompasses:

* configuration of the server;
* description of the **controllers**;
* definition of the **instruments**;

The configuration file
----------------------

All these components are configured in one file, located under a directory *.chimera* under your homedir; these are automatically generated for you the first time :program:`chimera` is run, if they don't already exist.

The file syntax is very simple: it uses YAML_, a very common format. Here is the default one:

.. literalinclude:: ../src/chimera/core/chimera.sample.config

.. _YAML: https://yaml.org/

Configuration syntax
^^^^^^^^^^^^^^^^^^^^

* Each section header goes in a line of its own, no spaces before nor after;
* Each subitem goes in a new line, indented; *no blank lines in between*;
* If a main item has more than one subitem, they are falgged by prepending a "- " to each.

With these rules in mind, lets examine the example above.

Server configuration
^^^^^^^^^^^^^^^^^^^^
::

    chimera:
        host: 127.0.0.1
        port: 7666

The server (the host where you ran the *chimera* script), is identified by the section header; it is followed by indented parameters *host* and *port*, indicating the network address:port of the server (remember chimera has distributed capabilities).

Site configuration
^^^^^^^^^^^^^^^^^^
::

    site:
        name: CTIO
        latitude: "-30:10:4.31"
        longitude: "-70:48:20.48"
        altitude: 2212
        flat_alt: 80
        flat_az : 10

This section describes your observatory's geolocation and the position for dome flats. Note the site coordinates are quoted.

Instruments configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

Every defined instrument carries a number of configuration options; please refer to the :ref:`Advanced` section for details.

Filter focus offsets
^^^^^^^^^^^^^^^^^^^^
::

    filterwheel:
        name: fake
        type: FakeFilterWheel
        filters: [U, B, V, R, I]
        focuser: /FakeFocuser/fake
        focus_offsets: {U: -100, B: 0, V: 0, R: 25}

Filters of different optical thickness need different focus positions. Point the wheel at a
*focuser* and give it a mapping of *focus_offsets*, in whatever units that focuser works in (steps,
microns, ...), and every filter change moves the focuser by the difference between the outgoing
and the incoming filter before ``set_filter()`` returns. Offsets are relative moves, so autofocus results and temperature compensation are
preserved. Filters left out of the table (``I`` above) get no offset.

Leave ``focuser`` unset to disable the compensation. If the offset cannot be applied the filter
change fails with a ``FocusOffsetException`` and the exposure never starts, so a focuser that
cannot reach position surfaces as an error instead of silently unfocused data.

This replaces the ``chimera-filterfocus`` plugin, whose ``focus_filters`` and ``focus_difference``
options map to the ``focus_offsets`` mapping above.

Automatic pier flip
^^^^^^^^^^^^^^^^^^^

::

    telescope:
        name: fake
        type: FakeTelescope
        pier_flip_ha: 0

A German equatorial mount cannot track indefinitely past the meridian: sooner or later the tube
runs into the pier. Set *pier_flip_ha* to the hour angle, in hours, where that becomes a problem
and the telescope re-slews to the position it is already pointing at as soon as tracking takes it
there, which is what makes the mount pick the other side of the pier. ``0`` flips at the meridian,
``0.5`` gives it another 30 minutes of tracking.

Only a mount that arrived at the limit *by tracking* is flipped; slewing straight to an object
that is already past it leaves the mount on whichever side its own driver chose. The flip fires
``slew_begin``/``slew_complete`` like any other slew, so a dome in ``track`` mode follows along.

Leave ``pier_flip_ha`` unset (the default) on a fork or alt-azimuth mount, which has nothing to
flip. This replaces the ``chimera-autopierchange`` plugin, whose ``ha_flip`` option maps to
``pier_flip_ha``.

Controllers Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

The controller section is slightly different in the sense that it allows for subsections; the same syntax rules apply. Once again, for a detailed description of options, see the :ref:`Advanced` section.

