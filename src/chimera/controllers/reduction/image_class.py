from pyraf import iraf


class Image:

  def __init__(self, filelocation, imname='None', ccdtype='None', imtype='None', filterset='None'):
    
    iraf.images.imutil.hedit(image = filelocation, fields = 'imtype',\
 value = imname, addonly = 'yes', verify = 'no')

    iraf.images.imutil.hedit(image = filelocation, fields = 'ccdtype',\
 value = ccdtype, addonly = 'yes', verify = 'no')

    iraf.images.imutil.hedit(image = filelocation, fields = 'filter',\
 value = filterset,  addonly = 'yes',verify = 'no')

    self.location = filelocation
 
    iraf.images.imutil.imgets(image = filelocation, param = 'title')
    imname = iraf.images.imutil.imgets.value
    self.name = imname
    
    iraf.images.imutil.imgets(image = filelocation, param = 'ccdtype')
    ccdtype = iraf.images.imutil.imgets.value
    self.ccd = ccdtype

    iraf.images.imutil.imgets(image = filelocation, param = 'imtype')
    imtype = iraf.images.imutil.imgets.value
    self.type = imtype
    
    iraf.images.imutil.imgets(image = filelocation, param = 'filter')
    filterset = iraf.images.imutil.imgets.value
    self.filter = filterset

    iraf.image.imutil.imgets(image = filelocation, param = 'date')
    dtime = iraf.image.imutil.imgets.value
    self.date = dtime

    iraf.image.imutil.imgets(image = filelocation, param = 'date-obs')
    obdtime = iraf.image.imutil.imgets.value
    self.obsdate = obdtime

    iraf.image.imutil.imgets(image = filelocation, param = 'exptime')
    extime = iraf.image.imutil.imgets.value
    self.exptime = extime

  def getParam(self, param):
    if param == 'name':
      return self.name
    elif param == 'ccdtype':
      return self.ccd
    elif param == 'imtype':
      return self.type
    elif param == 'filter':
      return self.filter
    elif param == 'date':
      return self.time
    elif param == 'date-obs':
      return self.obsdate
    elif parm == 'exptime':
      return self.exptime
    else:
      return 'None'

