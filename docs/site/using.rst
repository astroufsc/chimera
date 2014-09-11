Using Chimera 
=============

**Chimera** provides a few features to make your life easier when getting started with the system:

 - reasonable defaults;
 - fake devices as default when no configuration is supplied;
 - minimum boilerplate on command line once configured;
 - an easy to read/write configuration format: `YAML: YAML Ain't Markup
   Language <http://www.yaml.org>`_.

Once installed, Chimera provides a few command line programs:

 - :program:`chimera`
 - :program:`chimera-tel`
 - :program:`chimera-cam`
 - :program:`chimera-dome`
 - :program:`chimera-focus`
 - :program:`chimera-admin`


Starting Chimera
----------------

To start the server component of the software, run:

::

	chimera [-v|v]

This will start the server, with either the device set described in the configuration file or the set of default ones provided if no configuration is present.

Using the Chimera scripts
-------------------------

Every script has a *--help* option that displays usage information in great detail; here we will provide a few examples and/or use cases for your every day observing needs.

Additionally, all **chimera** scripts have a common set of options:

  --version
	show program's version number and exit
  -h, --help
	show this help message and exit
  -v, --verbose
	Display information while working
  -q, --quiet
	Don't display information while working
	[default=True]


**chimera-cam**
^^^^^^^^^^^^^^^

Say you want to take two frames of 10 seconds each and save to file names like :file:`fake-images-XXXX.fits`::

 chimera-cam --frames 2 --exptime 10 --output fake-images


**chimera-dome**
^^^^^^^^^^^^^^^^

In routine operations, the dome and the telescope devices are synchronized; it is however possible to move either independently::

	chimera-dome --to=AZ

**chimera-tel**
^^^^^^^^^^^^^^^

Slew the scope::

 chimera-tel --slew --object M5

As noted before, the dome will follow the telescope's position automatically. If the dome is still
moving, :program:`chimera-cam` will wait until the dome finishes::

 chimera-cam --frames 1 --filters R,G,B --interval 2 --exptime 30

After about one and a half minute, you'll have three nice frames of M5 in R, G and B
filters, ready to stack and make nice false color image.

**chimera-filter**
^^^^^^^^^^^^^^^^^^

This script controls a configured (or fake) filter wheel::

	chimera-filter [-F|--list-filters]

	chimera-filter [-f |--set-filter=] FILTERNAME

The former command will list the filters configured in :program:`chimera` (or the fakes), the latter moves the filter wheel to the position referred to by the filter's name.

