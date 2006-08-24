#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.59)
AC_INIT([uts], [1.0RC1], [henrique@astro.ufsc.br] )
AC_CONFIG_SRCDIR([src/sec/main.c])
AM_INIT_AUTOMAKE

AC_DEFINE([PROGRAM_URL], ["http://www.astro.ufsc.br/"], [ ])

# Checks for programs.
AC_PROG_CXX
AC_PROG_CC
AC_PROG_CPP
AC_PROG_INSTALL
AC_PROG_LN_S
AC_PROG_MAKE_SET
AC_PROG_RANLIB

# Python stuff
AM_PATH_PYTHON

# which distro?
UTS_CHECK_DISTRO

# Checks for header files.
AC_HEADER_DIRENT
AC_HEADER_STDC
AC_HEADER_SYS_WAIT
AC_CHECK_HEADERS([fcntl.h limits.h netdb.h netinet/in.h stdlib.h string.h strings.h sys/socket.h sys/time.h termios.h unistd.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_HEADER_STDBOOL
AC_C_CONST
AC_TYPE_SIZE_T
AC_HEADER_TIME
AC_STRUCT_TM

# Checks for library functions.
AC_FUNC_ERROR_AT_LINE
AC_REPLACE_FNMATCH
AC_FUNC_FORK
AC_FUNC_MALLOC
AC_FUNC_SELECT_ARGTYPES
AC_TYPE_SIGNAL
AC_CHECK_FUNCS([alarm floor memset pow select sqrt strcasecmp strchr strncasecmp strrchr])

# Checks for libraries.
AC_CHECK_LIB([m], [sin], [AC_DEFINE([HAVE_LM], [1], [Have C Math Library])])
AC_CHECK_LIB([jpeg], [jpeg_set_quality], [AC_DEFINE([HAVE_JPEG], [1], [Have libjpeg])])

# outputs
AM_CONFIG_HEADER([config.h])
AC_CONFIG_FILES([
		 Makefile
                 src/Makefile

		 src/drivers/Makefile
                 src/drivers/camfits.fake/Makefile
                 src/drivers/camfits.st4/Makefile
                 src/drivers/camfits.st7/Makefile
                 src/drivers/telgo.fake/Makefile
                 src/drivers/telgo.lx200/Makefile
                 src/drivers/telgo.paramount/Makefile
		 src/drivers/weather.wx200/Makefile

		 src/sec/Makefile

		 src/tools/Makefile
                 src/tools/client/Makefile

                 src/config/Makefile
		 src/config/initscripts/Makefile
		 src/config/initscripts/redhat/Makefile
		 src/config/initscripts/redhat/uts
		 src/config/initscripts/suse/Makefile
		 src/config/initscripts/suse/uts
		 src/config/initscripts/debian/Makefile
		 src/config/initscripts/debian/uts
	
                 src/python/Makefile
                 src/python/uts/Makefile
                 src/python/uts/core/Makefile
                 src/python/uts/instruments/Makefile
                 src/python/uts/interfaces/Makefile
	
		 contrib/Makefile
		 contrib/bin/Makefile
		 contrib/bin/sbig_load_lpt
		 contrib/bin/sbig_load_usb
		 contrib/bin/sbig_load_usb_suse
 		 contrib/fits2jpeg/Makefile
		 contrib/lib/Makefile]) 

AC_OUTPUT


