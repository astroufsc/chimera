# UTS_CHECK_DISTRO

AC_DEFUN([UTS_CHECK_DISTRO], [

	AC_MSG_CHECKING([which distro we are running on])

	if test -a /etc/SuSE-release; then

		distro=suse
		initconfig=/etc/sysconfig

	elif test -a /etc/redhat-release; then

		distro=redhat
		initconfig=/etc/sysconfig


	elif test -a /etc/debian_version; then

		distro=debian
		initconfig=/etc/default

	else
		distro=suse
	fi

	AC_SUBST([UTS_DISTRO], $distro)
	AC_SUBST([UTS_INITCONFIG_DIR], $initconfig)

	AC_MSG_RESULT([$distro])

])



