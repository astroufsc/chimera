from chimera.core.chimeraobject import ChimeraObject
from chimera.interfaces.cameradriver import Bitpix
from chimera.interfaces.camera import Shutter
from chimera.core.exceptions import ChimeraValueError
import Pyro.util
import logging
import chimera.core.log
log = logging.getLogger(__name__)

class ImageRequest(dict):
    
    def __init__(self, *args, **kwargs):
        __config__ =  {'exp_time':              1.0,
                       'frames':                1,
                       'interval':              0.0,
                       'shutter':               "OPEN",
                       'binning':               None,
                       'window':                None,
                       'readOnAbort':           False,
                       'bitpix':                Bitpix.uint16,
                       'filename':              '$date',
                       'headers':               [],
                       'image_type':             'object',

                       #URLs of proxies from which to get metadata before taking each image
                       'metadatapre':           [],

                       #URLs of proxies from which to get metadata after taking each image
                       'metadatapost':          [],

                       #Headers accumulated during processing of each frame (=headers+metadatapre+metadatapost)
                       'accum_headers':         [],
                       }
        
        for k,v in __config__.items():
            self[k]=v
        
        for k,v in kwargs.items():
            self[k]=v
        
        for a in args:
            for k,v in a.items():
                self[k]=v
    
        
        forceArgsValid = kwargs.get('forceArgsValid', False)

        if self['exp_time'] < 0.0:
            if forceArgsValid:
                self.exp_time = 0.0
            else:
                raise ChimeraValueError('Invalid exposure length (<0 seconds).')
        
        if self['frames'] < 1:
            if forceArgsValid:
                self.frames = 1
            else:
                raise ChimeraValueError('Invalid number of frames (<1 frame).')
        
        if self['interval'] < 0.0:
            if forceArgsValid:
                self.interval = 0.0
            else:
                raise ChimeraValueError('Invalid interval between exposures (<0 seconds)')

        if str(self['shutter']) not in Shutter:
            if forceArgsValid:
                self.shutter = Shutter.LEAVE_AS_IS
            else:
                raise ChimeraValueError('Invalid shutter value: ' + str(self['shutter']))
    
    def addDict(self, *args):
        for a in args:
            for k,v in a.items():
                self[k]=v
    
    def addPreHeaders(self, manager):
        self['accum_headers']=[]
        self['accum_headers']+=self['headers']
        for proxyurl in self['metadatapre']:
            try:
                proxy = manager.getProxy(proxyurl)
                self['accum_headers']+=proxy.getMetadata()
            except Exception, e:
                log.warning('Unable to get metadata from ' + proxyurl)
                print ''.join(Pyro.util.getPyroTraceback(e))

    
    def addPostHeaders(self, manager):
        for proxyurl in self['metadatapost']:
            proxy = manager.getProxy(proxyurl)
            try:
                proxy = manager.getProxy(proxyurl)
                self['accum_headers']+=proxy.getMetadata()
            except:
                log.warning('Unable to get metadata from ' + proxyurl)
    
    def __str__(self):
        return ('Duration: %f, Frames: %i, Shutter: %s, image_type: %s' % (self['exp_time'],self['frames'],self['shutter'],self['image_type']))
