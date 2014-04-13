import sys
from chimera.core.event import event

try:
    from astropy.io import fits
except:
    import pyfits as fits
import numpy as np

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ObjectNotFoundException

from chimera.interfaces.guider import Guider

from chimera.instruments.filterwheel import FilterWheelBase

#import chimera.core.log
# import logging
#
# log = logging.getLogger(__name__)

class ChimeraGuider(ChimeraObject, Guider):

    def __init__(self):
        ChimeraObject.__init__(self)

    def __start__(self):
        """
        Initialization stuff for the guider:

        """
        self.gboxes = list()
        self.gimages = list()
        self.centroids = list()

        try:
            t, gc, mc = (self.getManager().getProxy(self[x]) for x in ['telescope','guidercamera','camera'])
        except ObjectNotFoundException, e:
            self.log.debug('%s Component not found' % e)
            #print('%s' % sys.exc_info()[1])
            # TODO: better exit strategy
            return
        else:
            if not (x.ping for x in [t,gc,mc]):
                print('Component not responding')
                return

        mc.exposeBegin += self.exposeBegin
        mc.exposeEnd += self.exposeEnd

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
            # Store coords of all compliant guiding boxes.
            self.gboxes.append([(b[0] - 5, b[0] + 5), (b[1] - 5, b[1] + 5)])
            # ...and also store the corresponding image sections, until we know
            # how the cameras will deliver guider images.
            self.gimages.append(gdr_array[b[0] - 5:b[0] + 5, b[1] - 5:b[1] + 5])

    def getCOM(self, gf):
        """
        Get a guiding image ( of size gboxes); calculate the centroid, compare to
        reference (where it's at?) and return offsets (where are NESW!?)
        @param gf: guiding box as fits image.
        @rtype : list with centroid coordinates (pixels).
        """
        #ps = fits.getdata(gf)
        ps = gf
        n = np.sum(ps)

        # "Grid logic" (ha!) courtesy of scipy.ndimage.measurements.center_of_mass
        grids = np.ogrid[[slice(0, i) for i in ps.shape]]

        self.centroids.append([np.sum(ps*grids[dir]) / n for dir in range(ps.ndim)])

    # @event
    # def startGuider(self, fld):
    #     """
    #     """
    #     #Tip: use telescope.moveOffset(ra,dec).
    #     # First pass?
    #     if not len(self.gboxes):
    #         self.getGdrBoxes(fld)
    #         # Use the brightest box
    #         self.getCOM(self.gimages[0])
    #     # 2nd and on
    #     while not self.stopped:
    #

    def exposeBegin(self):
        pass

    def exposeEnd(self):
        pass
