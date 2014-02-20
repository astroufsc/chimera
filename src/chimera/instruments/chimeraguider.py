import threading
import sys

import numpy as np
from chimera.core.event import event

try:
    from astropy.io import fits
except:
    import pyfits as fits

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ObjectNotFoundException
from chimera.interfaces.guider import Guider

from chimera.instruments.filterwheel import FilterWheelBase

import logging

class ChimeraGuider(ChimeraObject, Guider):
    def __init__(self):
        ChimeraObject.__init__(self)

    def __start__(self):
        """
        Initialization stuff for the guider:

        """
        self.gboxes = list()

        # Turns out dome.py has exactly what I need... Shameless copy!
        try:
            t = self.getManager().getProxy(self['telescope'])
        except:
            self.log.exception('Cannot contact telescope instance.')
            return

        if not t.ping():
            self.log.exception('Telescope not responding! Unable to guide.')
            return

        try:
            c = self.getManager().getProxy(self['guidercamera'])
        except:
            self.log.exception('Guider camera not found! Unable to guide.')
            return

        if not c.ping():
            self.log.exception('Guider camera not responding! Unable to guide')
            return

    def getGdrBoxes(self, img):
        """
        Simple, unsophisticated, but (hopefully) fast guiding system
        """
        # Assume the data is in the primary header unit.

        gdr_array = fits.getdata(img)

        boxmin = np.nanvar(gdr_array)
        boxmax = np.nanmax(gdr_array)
        box_h = set()
        box_v = set()

        # Get the brightest candidates for guiding sources.
        # TODO: reimplement all this with grids, surely more efficient...
        for i in range(0, np.shape(gdr_array)[0]):
            if (1.5 * boxmin < np.nanmax(gdr_array[i, :]) <= boxmax):
                box_h.add((i, np.nanargmax(gdr_array[i, :])))
            else:
                continue

        for i in range(0, np.shape(gdr_array)[1]):
            if (boxmin < np.nanmax(gdr_array[:, i]) <= boxmax):
                box_v.add((np.nanargmax(gdr_array[:, i]), i))
            else:
                continue

        # All tuples present in both sets are the centers of potential gdr boxes.
        #TODO: check for objects too close to any border.

        # Finally, the guiding centers are:
        gcenters = box_h.intersection(box_v)
        lgcenters = list(gcenters)

        for b in lgcenters:
            print b; raw_input()
            self.gboxes.append([(b[0] - 5, b[0] + 5), (b[1] - 5, b[1] + 5)])


        # if self['gdr_saveimages']:
        #     n = fits.PrimaryHDU(gbox)
        #     hunits = fits.HDUList(n)
        #     hunits.writeto(os.path.join(self['gdrimagesdir'], "box.fits"))


    def com(self, gf):
        """
        Get a guiding image ( of size gboxes); calculate the centroid, compare to
        reference (where it's at?) and return offsets (where are NESW!?)
        @param gf: guiding box as fits image.
        @rtype : list with centroid coordinates (pixels).
        """
        ps = fits.getdata(gf)
        n = np.sum(ps)

        #"Grid logic" (ha!) courtesy of scipy.ndimage.measurements.center_of_mass
        grids = np.ogrid[[slice(0, i) for i in ps.shape]]

        ctrd = [np.sum(ps*grids[dir]) / n for dir in range(ps.ndim)]

        return ctrd

    @event
    def startGuider(self, pos):
        """
        """
        #Tip: use telescope.moveOffset(ra,dec).
        pass



