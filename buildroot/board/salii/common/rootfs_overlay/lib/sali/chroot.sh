#
# This file is part of SALI
#
# SALI is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SALI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SALI.  If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2010-2021 SURF

## Inspired/based on the arch-chroot script

###
# Usage: chroot_mount
#
# Mount the pseudo file-system so we can chroot and wrapper for the mount command
# accepts same arguments
#   
###
chroot_mount() {

    if [ -f "${SALI_CACHE_DIR}/mounts.chroot" ]
    then
        escaped_var=$(echo $1 | sed 's/\n/\n\n/g')
        rslt=$(egrep "^${escaped_var}" "${SALI_CACHE_DIR}/mounts.chroot")
        if [ -n "${rslt}" ]
        then
            return 0
        fi
    fi

    echo $@ >> $SALI_CACHE_DIR/mounts.chroot
    mount "$@"
}

###
# Usage: chroot_setup
#
# A function to setup all the pseudo file-systems
#   
###
chroot_setup() {
    chroot_mount proc "${SALI_TARGET}/proc" -t proc -o nosuid,noexec,nodev
    chroot_mount sys "${SALI_TARGET}/sys" -t sysfs -o nosuid,noexec,nodev,ro
    chroot_mount udev "${SALI_TARGET}/dev" -t devtmpfs -o mode=0755,nosuid
    chroot_mount devpts "${SALI_TARGET}/dev/pts" -t devpts -o mode=0620,gid=5,nosuid,noexec
    chroot_mount shm "${SALI_TARGET}/dev/shm" -t tmpfs -o mode=1777,nosuid,nodev
    chroot_mount /run "${SALI_TARGET}/run" --bind 
    chroot_mount tmp "${SALI_TARGET}/tmp" -t tmpfs -o mode=1777,strictatime,nodev,nosuid

    if [ "$(is_yes $SALI_EFI)" -eq 1 ]
    then
        modprobe efivarfs
	chroot_mount efivarfs "${SALI_TARGET}/sys/firmware/efi/efivars" -t efivarfs -o nosuid
    fi
}

