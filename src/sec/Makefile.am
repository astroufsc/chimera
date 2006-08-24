include $(top_srcdir)/rules.make

noinst_LIBRARIES = libsec.a

libsec_a_SOURCES = sec.c messages.c skterror.c sktlist.c fields.c  \
		   sec.h messages.h skterror.h sktlist.h fields.h

bin_PROGRAMS = sec

sec_SOURCES = server.c sec_config.c sec_server.c main.c \
	      server.h sec_config.h sec_server.h main.h
	      
sec_LDADD = -lsimpleskts -lsec
