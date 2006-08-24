include $(top_srcdir)/rules.make

bin_PROGRAMS = telgo.fake

telgo_fake_SOURCES = errors.h fields.c fields.h main.c ser.c ser.h

telgo_fake_LDADD = -lm -lcfitsio

uts_driver_DATA = fake.telescope.xml
