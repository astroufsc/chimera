
import warnings
import time
import os
import subprocess

try:
    # disable RO warning
    warnings.filterwarnings(action='ignore', module='RO.DS9')
    from RO.DS9 import DS9Win
    have_ds9 = True
except ImportError:
    have_ds9 = False


def xpaaccess(template="ds9"):

    p = subprocess.Popen("xpaaccess -v %s" % template, stdout=subprocess.PIPE, shell=True)
    p.wait()

    aps = p.stdout.read()

    aps = aps.split("\n")

    if len(aps):
        aps = [x for x in aps if len(x) >= 2]

    return aps

class DS9 (object):
    """
    A wrapper to enable programmatic control of DS9
    (http://www.astro.washington.edu/rowen/) instances. Thanks to
    Russel Owen (http://www.astro.washington.edu/rowen/) for great
    RO.DS9 module.
    """

    def __init__ (self, open=False):

        if not have_ds9:
            raise IOError("No DS9 available. Check if you have DS9 and XPA"
                          " installed and correctly accesible from Chimera's PATH.")

        id = "ds9"
        ids = xpaaccess()
        if ids:
            id = ids[-1]

        try:
            self.ds9 = DS9Win(doRaise=True, doOpen=open, template=id)
        except RuntimeError, e:
            # even with RO installed, we still need XPA package to get DS9 working
            raise IOError("DS9 is not available, check if you have the XPA package installed. Display disabled.")

    def open(self):
        self.ds9.doOpen()

    def isOpen(self):
        return self.ds9.isOpen()

    def quit(self):
        if self.isOpen():
            self.set("exit")            

    def displayImage (self, image):
        try:
            self.displayFile(image.filename())
        except IOError:
            self.dipslayFile(image.http())

    def displayFile (self, filename=None, url=None):
        """
        Display a file either from a local file or from a remote URL.

        @param filename: local filename.
        @type  filename: str

        @param url: remote URL
        @type  url: str

        @rtype: None
        """

        if not filename and not url:
            raise TypeError("You must pass either a filename or a url.")

        if filename:
            if not os.path.exists(filename):
                raise IOError("%s doesn't exists" % filename)

            self.set("file '%s'" % filename)

        if url:
            self.set("file url '%s'" % url)

    def displayArray (self, array):
        pass

    def set(self, cmd, data=None):
        self.ds9.xpaset(cmd, data)

    def get(self, cmd):
        return self.ds9.xpaget(cmd)

    def id (self):
        return self.ds9.template

