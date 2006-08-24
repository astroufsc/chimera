
uts_initddir = /etc/init.d
uts_initconfigdir = @UTS_INITCONFIG_DIR@

uts_etcdir = /etc/uts
uts_etc_secdir = /etc/uts/sec
uts_libdir = $(prefix)/lib

uts_driverdir = /etc/uts/drivers

AM_CFLAGS=-I$(top_srcdir)/contrib/include -I$(top_srcdir)/src/sec -I$(top_srcdir)/src/base

AM_LDFLAGS=-L$(top_srcdir)/contrib/lib -L$(top_srcdir)/src/sec -L$(top_srcdir)/src/base -Wl,-rpath=$(uts_libdir)

AM_CPPFLAGS=-I$(top_srcdir)/contrib/include -I$(top_srcdir)/src/sec -I$(top_srcdir)/src/base
