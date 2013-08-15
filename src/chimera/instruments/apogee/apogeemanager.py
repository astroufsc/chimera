#!/usr/bin/python

from ctypes import cdll
import ctypes as c
libc = cdll.LoadLibrary('libapogee_chimera.so')

class ApogeeManager(object):
    def __init__(self):
	    # ApogeeAltaManager* NewApogeeAltaManager(char* image_name, double time_exposure, 
	    # 	int shutter, int xbin, int ybin, int xstart, int xend, int ystart, int yend)
		#
		# image_name - path of file
		# time_exposure - exposure time is seconds 
		# xbin - Horizontal binning - Binning factor in x, default 1
		# xbin - Vertical binning - Binning factor in y, default 1
		# xstart - Region of interest - Image subregion in the format startx,starty,endx,endy
		# xend - Region of interest - Image subregion in the format startx,starty,endx,endy
		# ystart - Region of interest - Image subregion in the format startx,starty,endx,endy
		# yend - Region of interest - Image subregion in the format startx,starty,endx,endy

        self.obj = libc.NewApogeeAltaManager(1, 1, 0, 0, 0, 0)
        print "ApogeeManager - initalized"

    def setUp(self):
        libc.setUp(self.obj)

    def expose(self, filename, expose_time, shutter):
        libc.expose(self.obj, c.c_char_p(filename), c.c_double(expose_time), c.c_int(shutter) )

    def stop(self):
        libc.stop(self.obj)

    def startCooling(self, temperature):
        libc.startCooling(self.obj, c.c_double(temperature))

    def stopCooling(self):
        libc.stopCooling(self.obj)

    def getTemperature(self):
        libc.getTemperature.restype = c.c_double
        temperature = libc.getTemperature(self.obj)
        return temperature

    def getImageData(self):
        libc.getImagedata.restype = (c.c_ushort * 1024 * 1024 * 1024)()
        return libc.getImageData(self.obj) 

    def startFan(self):
        return libc.startFan(self.obj)

    def stopFan(self):
        return libc.stopFan(self.obj)        
