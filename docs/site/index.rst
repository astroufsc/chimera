
Chimera: Observatory Automation System
======================================

Chimera is a package to control astronomical observatories aiming the
creation of remote and even autonomous observatories with just a few
clicks. Using Chimera you can easily control telescopes, CCD cameras,
focusers and domes in a very integrated way.

**Distributed**
   Fully distributed system. You can use different machines to
   control each instrument and everything will looks like just one.

**Powerful**
   Very powerful autonomous mode. Give a target and exposure parameters
   and Chimera does the rest.

**Web interface**
   Web interface to schedule and monitor observations (`in development`).

**Hardware support**
   Support for most common off-the-shelf components. See `supported
   devices`_.

   Very easy to add support for new instruments (it's Python code!).

**Flexible**
   Chimera can be used in a very integrated mode but also in standalone
   mode to control just one instrument.

**Free**
   It's free (as in *free beer*) and written in a very modern
   language. Python!.

Getting started
---------------

To try out Chimera, follow the installation instructions and make sure
that you have at least one `supported devices`_.

The easiest way to install Chimera is to use `easy_install
<http://peak.telecommunity.com/DevCenter/EasyInstall>`_::

   sudo easy_install chimera-python

... and that's it! All dependencies are automagically installed.

You can also download the sources at `Chimera Development page
<http://code.google.com/p/chimera>`_ and try to install it *by hands*.

Use our `Quickstart <http://chimera.sf.net/quick-start>`_ document
to guide yout through the first steps of using Chimera. There is also a
`PDF <http://chimera.sf.net/quick-start/quick-start.pdf>`_ version as well.

Help and Development
--------------------

You can help Chimera development, we are always looking for
contributors. If you don't write code, no problem! You can write
documentation, help with this site, marketing. Everyone can help!

See our `Development <http://code.google.com/p/chimera>`_ page for
more information, to report a bug or just follow Chimera's development
closely.

To start coding, look at our `Getting Started with Chimera <http://chimera.sf.net/getting-started>`_ document.
You can download it in `PDF <http://chimera.sf.net/getting-started/getting-started.pdf>`_ as well.

.. _supported_devices:

Supported Devices
-----------------

**Telescopes**
   `Meade <http://www.meade.com>`_ based LX-200 (Meade, Losmandy).

   `Paramount ME <http://www.bisque.com>`_ using TheSky COM+ interfaces.

**CCD Cameras**
   `SBIG <http://www.sbig.com>`_ USB cameras.

**Focusers**
   `OPTEC <http://www.optecinc.com>`_  NGF-S

**Domes**
   COTE/LNA Dome (`LNA <http://www.lna.br>`_ specific).


In Development 
^^^^^^^^^^^^^^

**CCD Cameras**
   `Apogee <http://www.ccd.com>`_  USB/Ethernet cameras.

.. note::
   If you need support for any device which Chimera's doesn't
   support, call us and we can try to develop it or help you to do it.

License
-------

Chimera is Free/Open Software licensed by `GPL v2
<http://www.gnu.org/licenses/gpl.html>`_ or later (at your choice).


Authors
-------

Chimera is mainly developed by Paulo Henrique Silva
<ph.silva@gmail.com> at `Universidade Federal de Santa Catarina
<http://www.ufsc.br>`_ in collaboration with his advisor Antonio
Kanaan.

Chimera is sponsored by `Laboratorio Nacional de Astrofisica
<http://www.lna.br>`_ through a `CNPq <http://www.cnpq.br>`_ grant.


