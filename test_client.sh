#!/bin/sh
#
# This file is part of SALI
#
# SALI is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SALI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied:ta warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SALI.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2010-2015 SURFsara
#

## Let's force their location, this makes this script a lot more simpler
if [ ! -x "$(basename ${0})" ]
then
    echo "Please run this script only from the root project dir!"
    exit 1
fi

## Some variables
LATEST="ftp://ftp.surfsara.nl/pub/sali/sali-x86_64.tar.gz"
EXTRACT_FILES="sali-1.6.3/x86_64/initrd.img sali-1.6.3/x86_64/kernel"
ROOT_DIR=$(pwd)
BUILD_DIR=$ROOT_DIR/client-build
RSYNC_OPTS="-ar --exclude-from=$ROOT_DIR/client/files/rsync_exclude"

## We need the following commands, just make sure your PATH is correct!
CURL=$(which curl)
TAR=$(which tar)
QEMUIMG=$(which qemu-img)
QEMUSYS=$(which qemu-system-x86_64)
CPIO=$(which cpio)
BUNZIP2=$(which bunzip2)
RSYNC=$(which rsync)
TAIL=$(which tail)

chr(){
    printf \\$(($1/64*100+$1%64/8*10+$1%8))
}

## Check if it's a supported environment
case "$(uname -s)" in
    "Darwin"|"Linux")
        ## Go ahead
    ;;
    *)
        echo "Os type $(uname -s) is not supported"
        exit 1
    ;;
esac

## Very simple argument parser
case "${1}" in
    clean)
        echo "Removing $BUILD_DIR dir"
        if [ -d "$BUILD_DIR" ]
        then
            sudo rm -rf $BUILD_DIR
        fi
    ;;
    run)
        if [ ! -d "$BUILD_DIR" ]
        then
            mkdir $BUILD_DIR
        fi
        
        if [ ! -r "$BUILD_DIR/$(basename $LATEST)" ]
        then
            echo "DOWNLOADING SALI"
            $CURL $LATEST -o "$BUILD_DIR/$(basename $LATEST)"
        fi

        NEEDED_FILES=$($TAR tf "$BUILD_DIR/$(basename $LATEST)" | egrep "kernel|initrd"|grep -v bootdisk)
        for afile in $NEEDED_FILES
        do
            if [ ! -r "$BUILD_DIR/$afile" ]
            then
                $TAR --strip-components 2 -C $BUILD_DIR -xvf "$BUILD_DIR/$(basename $LATEST)" $afile >/dev/null 2>&1
            fi
        done

        if [ ! -r "$BUILD_DIR/test_disk.qcow2" ]
        then
            for n in $(seq 97 100)
            do
                $QEMUIMG create -f qcow2 $BUILD_DIR/test_disk_$(chr $n).qcow2 1G >/dev/null 2>&1
            done
        fi

        ## Add initrd.img generator
        if [ ! -e "${BUILD_DIR}/initrd.img.out" ]
        then
            $BUNZIP2 -sk "${BUILD_DIR}/initrd.img" >/dev/null 2>&1
        fi

        ### Make sure the old test_dir is gone
        if [ -d "$BUILD_DIR/initrd_test" ]
        then
            echo "Removing previous initrd_test dir"
            sudo rm -rf "$BUILD_DIR/initrd_test"
        fi

        echo "Unpacking cpio image"
        mkdir "${BUILD_DIR}/initrd_test"
        cd "${BUILD_DIR}/initrd_test" && $CPIO -id < ${BUILD_DIR}/initrd.img.out >/dev/null 2>&1

        echo "Just to be sure, remove all files in the startup.d and installer.d"
        rm $BUILD_DIR/initrd_test/etc/startup.d/*
        rm $BUILD_DIR/initrd_test/etc/installer.d/*
        rm $BUILD_DIR/initrd_test/etc/ssh/ssh_host*key*

        echo "Rsyncing the test files"
        $RSYNC $RSYNC_OPTS $ROOT_DIR/client/ $BUILD_DIR/initrd_test

        echo "Creating new initrd"
        sudo chown -R root:wheel "$BUILD_DIR/initrd_test"
        cd "$BUILD_DIR/initrd_test" && sudo find . | sudo cpio --quiet -o -H newc > $ROOT_DIR/client-build/initrd_test.img.out

        echo "Using cmdline from file files/cmdline"
        CMDLINE=$(cat $ROOT_DIR/client/files/cmdline | egrep -v "^#" | xargs)

        for n in $(seq 97 100)
        do
            DISKLINE="$DISKLINE-hd$(chr $n) $BUILD_DIR/test_disk_$(chr $n).qcow2 "
        done

        echo "Starting VM"
        $QEMUSYS -kernel $BUILD_DIR/kernel -initrd $BUILD_DIR/initrd_test.img.out \
            -append "$CMDLINE" -m 1024 -cpu Haswell -smp "cpus=2" \
            -redir :8022::22 -redir :8514::514 \
            $DISKLINE &

        echo "Just type ctr+c to exit"
        wait
    ;;
    server)
        sudo $RSYNC --daemon --config $ROOT_DIR/client/files/rsyncd.conf        
        cd "$ROOT_DIR/client/files" && python2 -m SimpleHTTPServer 8000
        
        RSYNCLOGFILE=$(cat $ROOT_DIR/client/files/rsyncd.conf | awk '/^log file/ {print $NF}')
        PIDNUMBER=$($TAIL -n 1 $RSYNCLOGFILE | awk '{print $3}' | sed -e 's/\[//g' -e 's/\]//g')
        sudo kill $PIDNUMBER
    ;;
    *)
        echo "Usage: ${0} <run|clean|server>"
    ;;
esac

