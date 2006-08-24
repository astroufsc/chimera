include $(top_srcdir)/rules.make

bin_PROGRAMS = camfits.st4

camfits_st4_SOURCES = camera.c  ccd.c  ser.c \
		      camera.h  ccd.h  ser.h

camfits_st4_LDADD = -lcfitsio -lm

uts_driver_DATA = st4.camera.xml
