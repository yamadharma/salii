#!/bin/sh

LATEST="ftp://ftp.surfsara.nl/pub/sali/sali-x86_64.tar.gz"
EXTRACT_FILES="sali-1.6.3/x86_64/initrd.img sali-1.6.3/x86_64/kernel"
BUILD_DIR=$(pwd)/build

CURL=$(which curl)
TAR=$(which tar)
QEMUIMG=$(which qemu-img)
QEMUSYS=$(which qemu-system-x86_64)

check_commands(){
    for cmd in $@
    do
        if [ ! -x "${cmd}" ]
        then
            echo "Could not find command ${cmd} or is not executable"
            exit 1
        fi
    done
}

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

case "${1}" in
    clean)
        echo "Removing $BUILD_DIR dir"
        if [ -d "$BUILD_DIR" ]
        then
            rm -rf $BUILD_DIR
        fi
    ;;
    run)
        check_commands $CURL $TAR $QEMUIMG $QEMUSYS
        
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

        $QEMUSYS -kernel $BUILD_DIR/kernel -initrd $BUILD_DIR/initrd.img -m 1024 -cpu Haswell -smp "cpus=2" -hda $BUILD_DIR/test_disk.qcow2 &
        
    ;;
    *)
        echo "Usage: ${0} <run|clean>"
    ;;
esac

echo "Test"
wait
