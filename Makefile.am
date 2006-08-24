include $(top_srcdir)/rules.make

SUBDIRS = src contrib

EXTRA_DIST = rules.make

#install-exec-hook:

# 	@echo "Creating UTS services..."

# 	@if [ @UTS_DISTRO@ = "suse" ]; then		\
# 		/sbin/insserv spmd;			\
# 		/sbin/insserv secd;			\
# 		/sbin/insserv camd;			\
# 		/sbin/insserv teld;			\
# 		/sbin/insserv sbigcam;			\
# 	fi;

# 	@if [ @UTS_DISTRO@ = "redhat" ]; then										\
# 		/sbin/chkconfig --del sbigcam; /sbin/chkconfig --add sbigcam; /sbin/chkconfig --level 345 sbigcam on;	\
# 		/sbin/chkconfig --del spmd;    /sbin/chkconfig --add spmd;    /sbin/chkconfig --level 345 spmd on;	\
# 		/sbin/chkconfig --del secd;    /sbin/chkconfig --add secd;    /sbin/chkconfig --level 345 secd on;	\
# 		/sbin/chkconfig --del camd;    /sbin/chkconfig --add camd;    /sbin/chkconfig --level 345 camd on;	\
# 		/sbin/chkconfig --del teld;    /sbin/chkconfig --add teld;    /sbin/chkconfig --level 345 teld on;	\
# 	fi;

# 	@if [ @UTS_DISTRO@ = "debian" ]; then			\
# 		/usr/sbin/update-rc.d sbigcam defaults 90;	\
# 		/usr/sbin/update-rc.d spmd defaults 91;		\
# 		/usr/sbin/update-rc.d secd defaults 92;		\
# 		/usr/sbin/update-rc.d teld defaults 93;		\
# 		/usr/sbin/update-rc.d camd defaults 94;		\
# 	fi;

# 	@if [ ! -d /var/log/uts ]; then                  		\
# 		@echo "Creating log directory... ( /var/log/uts )";	\
# 		mkdir /var/log/uts;                     		\
# 	fi;

#	@if [ -x @PYTHON@ ]; then					\
#		cd $(top_srcdir)/src/python;				\
#		@PYTHON@ setup.py build;				\
#		@PYTHON@ setup.py install;				\
#		cd $(top_srcdir);					\
#	fi;
