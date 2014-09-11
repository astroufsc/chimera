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

The file syntax is very simple: it uses YAML_, a very common format. Here is the default one::

	chimera:
	  host: 127.0.0.1
	  port: 7666
	
	site:
	  name: T80S
	  latitude: "-30:10:4.31"
	  longitude: "-70:48:20.48"
	  altitude: 2212
	  flat_alt: 2178
	  flat_az : 10
	
	telescope:
	  name: fake
	  type: FakeTelescope
	
	camera:
	  name: fake
	  type: FakeCamera
	
	focuser:
	  name: fake
	  type: FakeFocuser
	
	dome:
	  name: fake
	  type: FakeDome
	
	  mode: track
	  telescope: /FakeTelescope/fake
	
	controller:
	  - type: Autofocus
	    name: fake
	    camera: /FakeCamera/fake
	    filterwheel: /FakeFilterWheel/fake
	
	  - type: ImageServer
	    name: fake
	    httpd: True
	    autoload: False
	
	  - type: ChimeraGuider
	    name: guiding

.. _YAML: https://yaml.org/

Configuration syntax:
^^^^^^^^^^^^^^^^^^^^^

* Each section header goes in a line of its own, no spaces before nor after;
* Each subitem goes in a new line, indented; *no blank lines in between*;
* If a main item has more than one subitem, they are falgged by prepending a "- " to each.

With these rules in mind, lets examine the example above.

Server configuration:
^^^^^^^^^^^^^^^^^^^^^
::

	chimera:
	  host: 127.0.0.1
	  port: 7666

The server (the host where you ran the *chimera* script), is identified by the section header; it is followed by indented parameters *host* and *port*, indicating the network address:port of the server (remember chimera has distributed capabilities).

Site configuration:
^^^^^^^^^^^^^^^^^^^
::

	site:
	  name: T80S
	  latitude: "-30:10:4.31"
	  longitude: "-70:48:20.48"
	  altitude: 2212
	  flat_alt: 80
	  flat_az : 10

This section describes your observatory's geolocation and the position for dome flats. Note the site coordinates are quoted.

Instruments configuration:
^^^^^^^^^^^^^^^^^^^^^^^^^^

Every defined instrument carries a number of configuration options; please refer to the :ref:`Advanced` section for details.

Controllers Configuration:
^^^^^^^^^^^^^^^^^^^^^^^^^^

The controller section is slightly different in the sense that it allows for subsections; the same syntax rules apply. Once again, for a detailed description of options, see the :ref:`Advanced` section.

