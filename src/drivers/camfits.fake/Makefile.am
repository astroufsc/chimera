include $(top_srcdir)/rules.make

bin_PROGRAMS = camfits.fake

camfits_fake_SOURCES = ccd.c ccd.h errors.h main.c ser.c ser.h

camfits_fake_LDADD = -lm -lcfitsio

uts_driver_DATA = fake.camera.xml
