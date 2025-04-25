import warnings
import os
import subprocess

try:
    # disable RO warning
    warnings.filterwarnings(action="ignore", module="RO.DS9")
    from RO.DS9 import DS9Win

    have_ds9 = True
except ImportError:
    have_ds9 = False


def xpa_access(template="ds9"):

    try:
        p = subprocess.Popen(
            f"xpaaccess -v {template}", stdout=subprocess.PIPE, shell=True
        )
        p.wait()

        aps = p.stdout.read()

        aps = aps.split("\n")

        if len(aps):
            aps = [x for x in aps if len(x) >= 2]

        return aps

    except OSError:
        # xpaaccess not found
        return []


class DS9(object):
    """
    A wrapper to enable programmatic control of DS9
    (http://www.astro.washington.edu/rowen/) instances. Thanks to
    Russel Owen (http://www.astro.washington.edu/rowen/) for great
    RO.DS9 module.
    """

    def __init__(self, open=False):

        if not have_ds9:
            raise IOError(
                "No DS9 available. Check if you have DS9 and XPA"
                " installed and correctly accesible from Chimera's PATH."
            )

        id = "ds9"
        ids = xpa_access()
        if ids:
            id = ids[-1]

        try:
            self.ds9 = DS9Win(doRaise=True, doOpen=open, template=id, closeFDs=True)
        except RuntimeError:
            # even with RO installed, we still need XPA package to get DS9
            # working
            raise IOError(
                "DS9 is not available, check if you have the XPA package installed. Display disabled."
            )

    def open(self):
        self.ds9.doOpen()

    def is_open(self):
        return self.ds9.isOpen()

    def quit(self):
        if self.is_open():
            self.set("exit")

    def display_image(self, image, frame=1):

        if os.path.exists(image.filename):
            self.display_file(filename=image.filename, frame=frame)
        else:
            self.display_file(url=image.http(), frame=frame)

    def display_file(self, filename=None, url=None, frame=1):
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

        self.set(f"frame {frame}")

        if filename:
            if not os.path.exists(filename):
                raise IOError(f"{filename} doesn't exists")

            self.set(f"file '{filename}'")

        if url:
            self.set(f"file url '{url}'")

    def display_array(self, array, frame=1):
        pass

    def set(self, cmd, data=None):
        self.ds9.xpaset(cmd, data)

    def get(self, cmd):
        ret = self.ds9.xpaget(cmd)
        if ret:
            return ret[:-1]
        else:
            return None

    def id(self):
        return self.ds9.template
