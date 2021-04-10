#!/bin/bash
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
# Copyright 2010-2021 SURF
#

if [ ! -d "devel" ]
then
    echo "Unable to find the \"devel\" directory in the project root"
    exit 1
fi

for a_file in bzImage rootfs.cpio
do
    if [ ! -f "devel/${a_file}" ]
    then
        echo "Unable to locate the ${a_file} in the devel directory"
        exit 1
    fi
done

## Some static variables
ROOT_DIR=$(pwd)
DEVEL_DIR=${ROOT_DIR}/devel
RSYNC_OPTS="-ar --exclude-from=${ROOT_DIR}/devel/files/rsync_exclude"

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
    run)
        if [ ! -r "$DEVEL_DIR/test_disk.qcow2" ]
        then
            for n in $(seq 97 98)
            do
                $QEMUIMG create -f qcow2 $DEVEL_DIR/test_disk_$(chr $n).qcow2 50G >/dev/null 2>&1
            done
        fi

        echo "Using cmdline from file files/cmdline"
        INTERFACE=$(ip route show | awk '/^default/ {print $5}')
        SALI_IMAGESERVER=$(ip -4 -o addr show $INTERFACE | awk '{print $4}' | awk -F'/' '{print $1}')
        CMDLINE="SALI_IMAGESERVER=${SALI_IMAGESERVER} $(cat $DEVEL_DIR/files/cmdline | egrep -v "^#" | xargs)"

        for n in $(seq 97 98)
        do
            DISKLINE="$DISKLINE-hd$(chr $n) $DEVEL_DIR/test_disk_$(chr $n).qcow2 "
        done

        echo "Starting VM"
        $QEMUSYS -kernel $DEVEL_DIR/bzImage -initrd $DEVEL_DIR/rootfs.cpio \
            -append "$CMDLINE" -m 1024 -smp "cpus=2" \
            -net user,hostfwd=tcp::8022-:22 -net nic \
            $DISKLINE &

        echo "Just type ctr+c to exit"
        wait

        rm -f /tmp/sali_cmdline >/dev/null 2>&1
    ;;
    server)
        sudo $RSYNC --daemon --config $DEVEL_DIR/files/rsyncd.conf        
        cd "$ROOT_DIR/devel/files" && python3 -m http.server 8000
        
        RSYNCLOGFILE=$(cat $ROOT_DIR/devel/files/rsyncd.conf | awk '/^log file/ {print $NF}')
        PIDNUMBER=$($TAIL -n 1 $RSYNCLOGFILE | awk '{print $3}' | sed -e 's/\[//g' -e 's/\]//g')
        sudo kill $PIDNUMBER
    ;;
    *)
        echo "Usage: ${0} <run|clean|server>"
    ;;
esac
