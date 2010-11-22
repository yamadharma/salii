#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.
# This is adapted from the code I wrote for OpenHPI to do the same - Sean
#
# SI_CHECK_FAIL($LIBNAME,$PACKAGE_SUGGEST,$URL,$EXTRA)
#

AC_DEFUN([SI_CHECK_FAIL],
    [
    SI_MSG=`echo -e "- $1 not found!\n"`
    if test "x" != "x$4"; then
        SI_MSG=`echo -e "$SI_MSG\n- $4"`
    fi
    if test "x$2" != "x"; then
        SI_MSG=`echo -e "$SI_MSG\n- Try installing the $2 package\n"`
    fi
    if test "x$3" != "x"; then
        SI_MSG=`echo -e "$SI_MSG\n- or get the latest software from $3\n"`
    fi
    
    AC_MSG_ERROR(
!
************************************************************
$SI_MSG
************************************************************
)
    ]
)

AC_PREREQ(2.59)
AC_INIT(SALI, 1.4, sali@sara.nl)

# Checks for programs.
AC_PROG_CXX
AC_PROG_AWK
AC_PROG_YACC
AC_PROG_CC
AC_PROG_CPP
AC_PROG_LEX
case $LEX in
    :) SI_CHECK_FAIL(lex,flex,,You cannot build many components without the flex parser);;
esac
AC_PROG_LN_S
AC_PROG_MAKE_SET

AC_PATH_PROG(RSYNC, rsync)
if test -z "$RSYNC" ; then
    SI_CHECK_FAIL(rsync,,,
        [*** 'rsync' missing, please install or fix your PATH ***])
fi

AC_PATH_PROG(MKCRAMFS, mkcramfs)
if test -z "$MKCRAMFS"; then
    AC_PATH_PROG(MKCRAMFS, mkfs.cramfs)
    if test -z "$MKCRAMFS"; then
        SI_CHECK_FAIL(mkcramfs,,,
            [*** 'mkcramfs' or 'mkfs.cramfs' not found, please install cramfs tools or fix your PATH ***])
    fi
fi


#
#  All the above checks were generated with autoscan, adjust as required, but they 
#  seem fine for now
#

AC_PATH_PROG(gcc_exec,gcc)
AC_PATH_PROG(gxx_exec,g++)
AC_SUBST(GCC,$gcc_exec)
AC_SUBST(GXX,$gxx_exec)

# parted needs uuid
AC_CHECK_LIB([uuid], [uuid_generate], [have_uuid=yes], [
	SI_CHECK_FAIL(libuuid,e2fsprogs-devel)
	])

# parted needs readline 

AC_CHECK_LIB([ncurses],[keyok],[LIBS="-lncurses"],
	     [SI_CHECK_FAIL(ncurses,ncurses-devel)])

AC_CHECK_LIB([readline],[rl_initialize],[have_readline=yes], [
	     SI_CHECK_FAIL(readline,readline-devel)])

# do we have devmapper
AC_CHECK_HEADERS([libdevmapper.h],[have_libdevmapper=yes])

AC_ARG_ENABLE([lvm],
    [  --enable-lvm            include lvm support [default=yes] if possible],
    [if test "x$enableval" = "xyes"; then
	if test "x$have_libdevmapper" = "xyes"; then
	    AC_SUBST(BUILD_LVM,1)
	else
	    SI_CHECK_FAIL(libdevmapper,libdevmapper-devel,,
	    [libdevmapper is required for lvm support.  You can build without
	     lvm support by passing the --disable-lvm flag])
	fi
     fi
    ],
    [if test "x$have_libdevmapper" = "xyes"; then
	AC_SUBST(BUILD_LVM,1)
     fi])

# for

AC_CONFIG_FILES([Makefile])

AC_OUTPUT
