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
        filters: "U B V R I"
        focuser: /FakeFocuser/fake
        focus_offsets: "U:-100 B:0 V:0 R:25"

Filters of different optical thickness need different focus positions. Point the wheel at a
*focuser* and give it a table of *focus_offsets*, in whatever units that focuser works in (steps,
microns, ...), and every filter change moves the focuser by the difference between the outgoing
and the incoming filter before ``set_filter()`` returns. Offsets are relative moves, so autofocus results and temperature compensation are
preserved. Filters left out of the table (``I`` above) get no offset.

Leave ``focuser`` unset to disable the compensation. If the offset cannot be applied the filter
change fails with a ``FocusOffsetException``; set ``focus_offset_required: false`` to only log the
error and carry on.

This replaces the ``chimera-filterfocus`` plugin, whose ``focus_filters`` and ``focus_difference``
options map to the ``focus_offsets`` table above.

Controllers Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

The controller section is slightly different in the sense that it allows for subsections; the same syntax rules apply. Once again, for a detailed description of options, see the :ref:`Advanced` section.

