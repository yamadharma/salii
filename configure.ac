#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.
# This is adapted from the code I wrote for OpenHPI to do the same - Sean
#

AC_PREREQ(2.59)
AC_INIT(SALI, m4_esyscmd([cat VERSION | tr -d '\n']), sali@sara.nl)

# Checks for programs.
AC_PROG_CXX
AC_PROG_AWK
AC_PROG_CC
AC_PROG_CPP
AC_PROG_LN_S
AC_PROG_MAKE_SET

AC_PATH_PROG(gcc_exec,gcc)
AC_PATH_PROG(gxx_exec,g++)
AC_SUBST(GCC,$gcc_exec)
AC_SUBST(GXX,$gxx_exec)

# Operatingsystem detection
AC_MSG_CHECKING([uname -s for detecting host operating system])
case "$(uname -s)" in
	Linux*)
		if [ test -e /etc/debian_version ]; then
			OS=debian
			OS_RELEASE=$(cat /etc/debian_version|awk -F . '{print $1}')
			AC_MSG_RESULT(found ${OS} release ${OS_RELEASE})
		elif [ test -e /etc/SuSE-release ]; then
			OS=suse
			OS_RELEASE=$(cat /etc/SuSE-release|awk '/VERSION =/ {print $3}')
			AC_MSG_RESULT(found ${OS} release ${OS_RELEASE})
		elif [ test -e /etc/redhat-release ]; then
			OS=rhel
			OS_RELEASE=$(cat /etc/redhat-release|awk '{print $3}')
			AC_MSG_RESULT(found ${OS} release ${OS_RELEASE})
		else
			AC_MSG_RESULT(no)
			AC_MSG_ERROR(Found an unsupported Linux distribution)
		fi
	;;
	*)
		AC_MSG_RESULT(no)
		AC_MSG_ERROR(Found an unsupported operating system)
	;;
esac

# Architecture detection
AC_MSG_CHECKING([uname -m for detecting host operating architecture])
case "$(uname -m)" in
	amd64*|x86_64)
		ARCH=x86_64
		ARCH_BIT=64
		AC_MSG_RESULT(found ${ARCH})
	;;
	ppc64*)
		ARCH=ppc64
		ARCH_BIT=64
		AC_MSG_RESULT(found ${ARCH})
	;;
	i686*|i386*)
		AC_MSG_RESULT(found ${ARCH})
		ARCH=i386
		ARCH_BIT=32
	;;
	*)
		AC_MSG_RESULT(no)
		AC_MSG_ERROR(Found an unsupported architecture)
		exit 1
	;;
esac

AC_SUBST(ARCH,$ARCH)
AC_SUBST(ARCH_BIT,$ARCH_BIT)
AC_SUBST(OS,$OS)
AC_SUBST(OS_RELEASE,$OS_RELEASE)
AC_SUBST(SALI_VERSION,"$(cat VERSION)")

AC_CONFIG_FILES([
	Makefile
	initrd/sali/bin/sali_functions
])

AC_OUTPUT
