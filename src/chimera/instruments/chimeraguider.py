import threading
import os

import numpy as np

try:
    from astropy.io import fits
except:
    import pyfits as fits

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.manager import ManagerAdapter
from chimera.core.lock import lock
from chimera.core.event import event

from chimera.interfaces.guider import Guider

from chimera.instruments.telescope import TelescopeBase
from chimera.instruments.filterwheel import FilterWheelBase

from chimera.util.filenamesequence import FilenameSequence

__all__  = ['ChimeraGuider']


class ChimeraGuider(ChimeraObject, Guider):
    def __init__(self):
        ChimeraObject.__init__(self)

    # def __start__(self):
    #     """
    #     Initialization stuff for the guider:
    #
    #     """
    #     pass

    def getTelescope(self):
        """
        Get the telescope we are guiding either from the __config__
        or from the running Manager, if needed. The latter should
        take precedence if different from the former (possible?).
        """
        return self.getManager().getProxy(self["telescope"])


    def correctTelPos(self, pos):
        """
        Send direction and distance (in arcseconds or pixels?) to the telescope
        for correction, if the guiding algorithm does not deliver them
        directly (hence this method might prove unnecessary, except for
        decoupling).
        @param pos: list of tuples (dir, dist); e.g.:
        [('S', 1.2), ('E', 0.4)]
        Constraints:
        - At most 2 elements in the list;
        - Cannot have opposing cardinals: N-S, or E-W, in the same list.
        Hint: use the SlewRate.GUIDE Enum
        """
        pass

    def getGdrBoxes(self, img):
        """
        We implement a SIMPLE, lightweight, guiding technique; for the purpose of
        keeping the scope aligned with the target, we don't need astrometry, photometry,
        nor field ID and WCS. We only need a clear point source of photons...
        """
        # Assume the data is in the primary header unit.
        # NOTE: need to hook an event here to know when the image is updated.

        gdr_array = fits.getdata(img)

        boxmin = np.nanvar(gdr_array)
        boxmax = np.nanmax(gdr_array)
        box_h = set()
        box_v = set()

        # Get the brightest candidates for guiding sources.
        for i in range(0, np.shape(gdr_array)[0]):
            if (1.5 * boxmin < np.nanmax(gdr_array[i, :]) <= boxmax):
                box_h.add((i, np.nanargmax(gdr_array[i, :])))
            else:
                continue

        for i in range(0, np.shape(gdr_array)[0]):
            if (boxmin < np.nanmax(gdr_array[:, i]) <= boxmax):
                box_v.add((np.nanargmax(gdr_array[:, i]), i))
            else:
                continue

        # All tuples present in both sets are the centers of potential gdr boxes.


        # Finally, the guiding boxes are:
        gboxes = box_h.intersection(box_v)
        return gboxes

        # if self['gdr_saveimages']:
        #     n = fits.PrimaryHDU(gbox)
        #     hunits = fits.HDUList(n)
        #     hunits.writeto(os.path.join(self['gdrimagesdir'], "box.fits"))



