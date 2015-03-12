#!/bin/sh
# test

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
RSYNC_OPTS="-ar --exclude-from=$ROOT_DIR/files/rsync_exclude"

## We need the following commands, just make sure your PATH is correct!
CURL=$(which curl)
TAR=$(which tar)
QEMUIMG=$(which qemu-img)
QEMUSYS=$(which qemu-system-x86_64)
CPIO=$(which cpio)
BUNZIP2=$(which bunzip2)
RSYNC=$(which rsync)

## Check if it's a supported environment
case "$(uname -s)" in
    "Darwin"|"Linux")
        if [ "$(uname -s)" == "Linux" ]
        then
            echo "Linux had not been tested, but should work"
        fi
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
            $QEMUIMG create -f qcow2 $BUILD_DIR/test_disk.qcow2 100G >/dev/null 2>&1
        fi

        ## Add initrd.img generator
        if [ ! -e "$ROOT_DIR/build/initrd.img.out" ]
        then
            echo "Bunzipping initrd.img"
            $BUNZIP2 -sk "$ROOT_DIR/build/initrd.img" >/dev/null 2>&1
        fi

        ## Make sure the old test_dir is gone
        if [ -d "$BUILD_DIR/initrd_test" ]
        then
            echo "Removing previous initrd_test dir"
            sudo rm -rf "$BUILD_DIR/initrd_test"
        fi

        echo "Unpacking cpio image"
        mkdir "$BUILD_DIR/initrd_test"
        cd "$BUILD_DIR/initrd_test" && $CPIO -id < ../initrd.img.out >/dev/null 2>&1

        echo "Just to be sure, remove all files in the startup.d and installer.d"
        rm $BUILD_DIR/initrd_test/etc/startup.d/*
        rm $BUILD_DIR/initrd_test/etc/installer.d/*
        rm $BUILD_DIR/initrd_test/etc/ssh/ssh_host*key*

        echo "Rsyncing the test files"
        $RSYNC $RSYNC_OPTS $ROOT_DIR/client/ $BUILD_DIR/initrd_test

        echo "Creating new initrd"
        sudo chown -R root:wheel "$BUILD_DIR/initrd_test"
        cd "$BUILD_DIR/initrd_test" && sudo find . | sudo cpio --quiet -o -H newc > $ROOT_DIR/build/initrd_test.img.out

        echo "Using cmdline from file files/cmdline"
        CMDLINE=$(cat $ROOT_DIR/client/files/cmdline | egrep -v "^#" | xargs)

        echo "Starting VM"
        $QEMUSYS -kernel $BUILD_DIR/kernel -initrd $BUILD_DIR/initrd_test.img.out \
            -append "$CMDLINE" -m 1024 -cpu Haswell -smp "cpus=2" \
            -redir :8022::22 -redir :8514::514 \
            -hda $BUILD_DIR/test_disk.qcow2 &

        echo "Just type ctr+c to exit"
        wait
    ;;
    webserver)
        cd "$ROOT_DIR/client/files" && python -m SimpleHTTPServer 8000
    ;;
    *)
        echo "Usage: ${0} <run|clean>"
    ;;
esac

