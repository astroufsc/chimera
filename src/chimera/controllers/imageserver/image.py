from chimera.core.remoteobject import RemoteObject
from Pyro.errors import NamingError
from chimera.interfaces.cameradriver import Bitpix
from chimera.controllers.imageserver.imageuri import ImageURI
from chimera.core.exceptions import ClassLoaderException
import Pyro.util
from chimera.controllers.imageserver.imageserver import ImageServer
from chimera.core.version import _chimera_description_

fits_date_format = "%Y-%m-%dT%H:%M:%S"

import pyfits
import numpy
import os.path
import time

##TODO: Python2.4 Compatible hashlib
#try:
#    import hashlib
#    def hashFcn(filename):
#        file = open(filename, 'rb')
#        hash = hashlib.sha1(file.read()).hexdigest()
#        file.close()
#        return hash
#except:
#    import sha
#    def hashFcn(filename):
#        file = open(filename, 'rb')
#        hash = sha.new(file.read()).hexdigest()
#        file.close()
#        return hash


class Image(RemoteObject):
    
    def __init__(self, fileName = None):
        RemoteObject.__init__(self)
        
        self.imageServer = ImageServer.getImageServer()
        
        if fileName == None:
            self.path = None
            self.header = None
            self.hash = None
            self.myGUID = Pyro.util.getGUID()
        else:
            self.path = os.path.expanduser(fileName)
            self.path = os.path.expandvars(self.path)
            self.path = os.path.realpath(self.path)
            self.header = pyfits.getheader(fileName)
            self.myGUID = self.header['CHM_IMID']
        
        try:
            self.imageServer.registerImage(self)
        except Exception, e:
            print ''.join(Pyro.util.getPyroTraceback(e))
        pass
        
    def getID(self):
        return self.myGUID
#        if self.hash == None:
##            self.hash = hashFcn(self.path)
#            self.hash =  getGUID()
#        return self.hash

    def getPath(self):
        return self.path
    
    def getURI(self):
        return ImageURI(self.imageServer, self.getID())
    
    @staticmethod
    def imageFromFile(fileName):
        toReturn = ImageServer.getImageServer().getImageByPath(fileName)
        if not toReturn:
            toReturn = Image(fileName)
        return toReturn
            
    @staticmethod
    def imageFromImg(img, imageRequest, hdrs = []):
        image = Image()
        
        hdu = pyfits.PrimaryHDU(img)
        
        file_date = Image.formatDate(time.gmtime())
                                                                                            
        basic_headers = [("EXPTIME", float(imageRequest['exp_time']) or -1, "exposure time in seconds"),
                         ("DATE", file_date, "date of file creation"),
                         #("DATE-OBS", obs_date, "date of the start of observation"),       #From cameradriver
                         #("MJD-OBS", 0.0, "date of the start of observation in MJD"),      #Not needed
                         #("RA", "00:00:00", "right ascension of the observed object"),     #From telescope
                         #("DEC", "00:00:00", "declination of the observed object"),        #From telescope
                         
                         #TODO: Convert to current equinox
                         #("EQUINOX", 2000.0, "equinox of celestial coordinate system"),
                         #("RADESYS", "FK5",  "reference frame"),
                         
                         #("SECPIX", 0.0, "plate scale"),                                   #Added after all other stuff is in
                         
                         ("WCSAXES", 2, "wcs dimensionality"),
                         ("CRPIX1", 0.0, "coordinate system reference pixel"),
                         ("CRPIX2", 0.0, "coordinate system reference pixel"),
                         ("CRVAL1", 0.0, "coordinate system value at reference pixel"),
                         ("CRVAL2", 0.0, "coordinate system value at reference pixel"),
                         ("CTYPE1", '', "name of the coordinate axis"),
                         ("CTYPE2", '', "name of the coordinate axis"),
                         ("CUNIT1", '', "units of coordinate value"),
                         ("CUNIT2", '', "units of coordinate value"),
                         ("CD1_1", 1.0, "transformation matrix element (1,1)"),
                         ("CD1_2", 0.0, "transformation matrix element (1,2)"),
                         ("CD2_1", 0.0, "transformation matrix element (2,1)"),
                         ("CD2_2", 1.0, "transformation matrix element (2,2)"),
                         ("CREATOR", _chimera_description_, ""),
                         #('OBJECT', 'UNKNOWN', 'Object observed'),                        #Added by scheduler
                         #('TELESCOP', 'UNKNOWN', 'Telescope used for observation'),        #Added by telescope
                         #('PI', 'Chimera User', 'Principal Investigator'),                #Added by scheduler
                         ('IMAGETYP', imageRequest['image_type'], 'Image type'),
                         ('CHM_IMID',image.getID(), 'Chimera Internal Image ID')
                         ]

        #TODO: Implement bitpix support
        #Should be done just before writing
        #if imageRequest['bitpix'] == Bitpix.uint16:
        hdu.scale('int16', '', bzero=32768, bscale=1)
        
        for header in basic_headers + imageRequest['accum_headers'] + hdrs:
            hdu.header.update(*header)
        
        image.path = image.imageServer.getFileName(imageRequest['filename'])
        
        hduList = pyfits.HDUList([hdu])
        
        hduList.writeto(image.path)
        
        del hdu
        del hduList
        
        return image.getURI()
    
    @staticmethod
    def formatDate(date):
        if isinstance(date, float):
            date=time.gmtime(date)
        return time.strftime(fits_date_format, date)
    