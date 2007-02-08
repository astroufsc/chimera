import time

from sbig import *

s = SBIG()

t1 = time.time()

if not s.openDriver():
	print s.getError()
	exit(-1)

if not s.openDevice(SBIG.usb):
	print s.getError()
	exit(-1)

if not s.establishLink():
	print s.getError()
	exit(-1)

if not s.queryCCDInfo():
	print s.getError()
	exit(-1)

t2 = time.time()

print t2-t1

if not s.closeDevice():
	print s.getError()
	exit(-1)

if not s.closeDriver():
	print s.getError()

