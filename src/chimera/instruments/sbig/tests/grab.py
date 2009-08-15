import time
import numpy

from chimera.instruments.sbig.sbigdrv import SBIGDrv

#ccd = SBIGDrv.imaging
ccd = SBIGDrv.tracking

s = SBIGDrv()

t1 = time.time()
s.openDriver()
s.openDevice(SBIGDrv.usb)
s.establishLink()
s.queryCCDInfo()
t2 = time.time()
t_init = t2 -t1

t1 = time.time()
s.startExposure(ccd, 100, SBIGDrv.openShutter)
t2 = time.time()
t_start_exposure = t2 -t1

while s.exposing(ccd):
	pass

print "exposure complete"

s.endExposure(ccd)

t3 = time.time()

t_expose = t3 -t2

size = s.readoutModes[ccd][0].getSize()
img = numpy.zeros((size[1], size[0]))

t1 = time.time()
s.startReadout(ccd, 0)

i = 0
for line in range(s.readoutModes[ccd][0].height):
	img[i] = s.readoutLine(ccd, 0)
	i = i + 1

s.endReadout(ccd)
t2 = time.time()

t_readout = t2 -t1

import os
os.environ["NUMERIX"] = "numpy"

import pyfits

t1 = time.time()

hdu = pyfits.PrimaryHDU(img)
f = pyfits.HDUList([hdu])
f.writeto("first-light.fits")

t2 = time.time()

t_write = t2 - t1

print "cam init:", t_init
print "start exposure:", t_start_exposure
print "exposing:", t_expose
print "readout:", t_readout
print "write:", t_write

s.closeDevice()
s.closeDriver()

