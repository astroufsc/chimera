
Chimera Quick Start
===================

Chimera provides a few features to make your life easier when getting
started with the system, using:

 - reasonable defaults
 - no configuration to get started with fake devices
 - minimum boilerplate on command line once configured
 - an easy to read/write configuration format: `YAML: YAML Ain't Markup
   Language <http://www.yaml.org>`_.

you will start using Chimera very quickly.

Once installed, Chimera provides a few command line programs:

 - :program:`chimera`
 - :program:`chimera-tel`
 - :program:`chimera-cam`
 - :program:`chimera-dome`
 - :program:`chimera-focus`
 - :program:`chimera-admin`

Without any configuration, those programs will use fake devices, some
kind of simulator. This way you can test the command line programs
even without any real device on hands.

When configured, :program:`chimera` script can be used to start and
stop the system, while other :program:`chimera-` programs control
specific devices in a very integrated way.

Getting started
---------------

Installation
============

To install Chimera, in most cases, its just one command::

 easy_install chimera-python

First Light
===========

Say you want to take two frames of 10 seconds each and save to files names like :file:`fake-images-XXXX.fits`::

 chimera-cam --frames 2 --exptime 10 --output fake-images
 
Without specific configuration, Chimera will try to use device simulators instead of real hardware, to configure you
real camera, edit Chimera's configuration file:file:`chimera.config`:

.. literalinclude:: camera.yaml
   :language: yaml

After that, you can take some real images::

 chimera-cam --frames 2 --exptime 10 --output real-images 

Add configuration for real telescope and dome:

.. literalinclude:: telescope-dome.yaml
   :language: yaml

Start Chimera's server mode to enable device integration::

 chimera -vv

Slew the scope::

 chimera-tel --slew --object M5

Dome will follow telescope position automatically. If dome still
moving, :program:`chimera-cam` will wait until dome finishes::

 chimera-cam --frames 1 --filters R,G,B --interval 2 --exptime 30

After about one and a half minute, you'll have three nice frames of M5 in R, G and B
filters, ready to stack and make nice false color image.


