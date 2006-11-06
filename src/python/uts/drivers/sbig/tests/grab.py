import time
import sys
import numpy

from sbig import *

s = SBIG()

t1 = time.time()
s.openDriver()
s.openDevice(SBIG.usb)
s.establishLink()
s.queryCCDInfo()
t2 = time.time()
t_init = t2 -t1

t1 = time.time()
s.startExposure(SBIG.imaging, 100, SBIG.openShutter)
t2 = time.time()
t_start_exposure = t2 -t1

while s.exposing(SBIG.imaging):
	pass

print "exposure complete"

s.endExposure(SBIG.imaging)

t3 = time.time()

t_expose = t3 -t2

img = numpy.zeros(s.readoutModes[SBIG.imaging][0].getSize())

t1 = time.time()
s.startReadout(SBIG.imaging, 0)

i = 0
for line in range(s.readoutModes[SBIG.imaging][0].height):
	img[i] = s.readoutLine(SBIG.imaging, 0)
	i = i + 1

s.endReadout(SBIG.imaging)
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

