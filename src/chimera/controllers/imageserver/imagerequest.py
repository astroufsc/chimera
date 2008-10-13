
from chimera.interfaces.cameradriver import Bitpix
from chimera.interfaces.camera import Shutter

from chimera.core.exceptions import ChimeraValueError

import Pyro.util

import logging
import chimera.core.log
log = logging.getLogger(__name__)


class ImageRequest (dict):
    
    def __init__(self, **kwargs):

        default = {'exptime' : 1.0,
                   'frames'  : 1,
                   'interval': 0.0,
                   'shutter' : Shutter.OPEN,
                   'binning' : None,
                   'window'  : None,
                   'bitpix'  : Bitpix.uint16,
                   'filename': '$DATE-$TIME',
                   'type'    : 'object'}

        # Automatically call getMetadata on all instruments + site as long as only
        # one instance of each is listed by the manager.
        self.auto_collect_metadata = True
        
        # URLs of proxies from which to get metadata before taking each image
        self.metadataPre = []

        # URLs of proxies from which to get metadata after taking each image
        self.metadataPost = []
        
        # Headers accumulated during processing of each frame (=headers+metadatapre+metadatapost)
        self.headers = []

        self.update(default)

        # validate keywords passed
        not_valid = [k for k in kwargs.keys() if k not in default.keys()]

        if any(not_valid):
            if len(not_valid) > 1:
                msg = "Invalid keywords: "
                for k in not_valid:
                    msg += "'%s', " % str(k)
                msg = msg[:-2]

            else:
                msg = "Invalid keyword '%s'" % str(not_valid[0])

            raise TypeError(msg)

        self.update(kwargs)

        # Used so that we don't take metadata twice from the same object
        self._accum_from = []  
    
        # do some checkings
        if self['exptime'] < 0.0:
            raise ChimeraValueError('Invalid exposure length (<0 seconds).')
        
        # FIXME: magic number here! But we shouldn't allow arbitrary maximum for safety reasons.
        if self['exptime'] > 12*60*60:
            raise ChimeraValueError('Invalid exposure. Must be lower them 12 hours.')

        if self['frames'] < 1:
            raise ChimeraValueError('Invalid number of frames (<1 frame).')
        
        if self['interval'] < 0.0:
            raise ChimeraValueError('Invalid interval between exposures (<0 seconds)')

        if str(self['shutter']) not in Shutter:
            raise ChimeraValueError('Invalid shutter value: ' + str(self['shutter']))

    def __str__(self):
        return ('exptime: %f, frames: %i, shutter: %s, type: %s' % (self['exptime'],
                                                                    self['frames'],
                                                                    self['shutter'],
                                                                    self['type']))
    
    def fetchPreHeaders (self, manager):
        auto = []
        if self.auto_collect_metadata:
            for cls in ('Site', 'Camera', 'Dome', 'FilterWheel', 'Focuser', 'Telescope'):
                classes = manager.getResourcesByClass(cls)
                if len(classes) == 1:
                    auto.append(str(classes[0]))

        self._getHeaders(manager, auto+self.metadataPre)

    def fetchPostHeaders (self, manager):
        self._getHeaders(manager, self.metadataPost)
        
    def _getHeaders (self, manager, proxies):

        for proxyurl in proxies:
            
            try:
                proxy = manager.getProxy(proxyurl)
                proxyLoc = str(proxy.getLocation())
                if proxyLoc not in self._accum_from:
                    self._accum_from.append(proxyLoc)
                    self.headers += proxy.getMetadata()
            except Exception, e:
                log.warning('Unable to get metadata from %s' % (proxyurl))
                print ''.join(Pyro.util.getPyroTraceback(e))
