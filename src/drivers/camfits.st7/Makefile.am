include $(top_srcdir)/rules.make

bin_PROGRAMS = camfits.st7 ccdcap

camfits_st7_SOURCES = csbigimg.h csbigimg.cpp csbigcam.h csbigcam.cpp getindex.h getindex.c main.cpp
camfits_st7_LDADD = -lm -lcfitsio -lsbigudrv

ccdcap_SOURCES = ccdcap-test.cpp ccdcap.h sbigcamcap.cpp sbigcamcap.h csbigimg.h csbigimg.cpp csbigcam.h csbigcam.cpp
ccdcap_LDADD = -lsbigudrv

uts_driver_DATA = st7.camera.xml
