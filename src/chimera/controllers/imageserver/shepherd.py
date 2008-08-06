from chimera.interfaces.camerang import Shutter

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.exceptions import ChimeraValueError

class Shepherd(ChimeraObject):
    """
    The shepherd will be responsible for guiding an image.
    
    It is created by a call to imageserver requesting a shepherd.
    This call will include the exposure paramaters and the specific
    camera instrument to use.
    
    Also passed will be a link to the telescope to retrieve pointing 
    information.
    """

#expose (self, exp_time,
#                frames=1, interval=0.0,
#                shutter=Shutter.OPEN,
#                binning=Binning._1x1,
#                window=Window.FULL_FRAME,
#                filename="$HOME/images/$date.fits"):

    __config__  = {'imageServerURI':        '/ImageServer/0',
                   'cameraURI':             '/Camera/0',
                   'fwheelURI':             '/FilterWheel/0',
                   'telescopeURI':          '/Telescope/0',
                   'exp_time':              1.0,
                   'frames':                1,
                   'interval':              0.0,
                   'shutter':               Shutter.LEAVE_AS_IS
                   'binning':               ('None', None),                 #Based upon camera.getBinnings
                                                # (('1x1', 3), ('2x2', 323))
                   'filter':                ('Clear', 'CLEAR'),             #Based upon filter.getFilters
                   'window':                ('Full', (0.5, 0.5, 1.0, 1.0)), #Ignored if hardware cannot handle
                   'chip':                  ('Default', None),              #Based upon camera.getChips
                   'readOnAbort':           False
                   }
    
    def __init__(self, **kwargs):
        
        ChimeraObject.__init__()
        
        self += kwargs
        
        forceArgsValid           = kwargs.get('forceArgsValid', False)

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

        if self['shutter'] not in Shutter.values():
            if forceArgsValid:
                self.shutter = Shutter.LEAVE_AS_IS
            else:
                raise ChimeraValueError('Invalid shutter value')
        
        try:
            filterwheel = self.getManager().getProxy(self.fwheel)
        except:
            pass
        
        if filterwheel:
            if self['filter'][1] not in filterwheel.getFilters():
                #Cannot force this valid without making too many assumptions!
                raise ChimeraValueError('Invalid filter value')
    
    def takeExposure(self):
        self.log.debug('Acquiring proxies...')
        camera      = self.getManager().getProxy(self['instrument'])
        camdriver   = camera.getDriver()
        filterwheel = self.getManager().getProxy(self['fwheel'])
        fwdriver    = filterwheel.getDriver()
        
        self.log.debug('Setting filter...')
        filterwheel.setFilter(self['filter'][1])
        
        tempStart   = camera.getTemperature()
        
        for expNo in range(1,self['frames']):
            data = camera.expose(self)
            
        
        self.getManager().getProxy(self['imageServerURI']).register(self)
    
    def callForReduction(self):
        
        pass
    
    

#camera.expose(a=a, b=b, c=c, ...)
#
#Image = camera.expose(ImageRequest(a=a, b=b, c=c, ...))
