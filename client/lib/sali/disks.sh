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
# Copyright 2010-2015 SURFsara

###
# $Id$
# $URL$
###

###
# Usage: disks_detect_lscsi
#
# Detect all disks using the lsscsi command
###
disks_detect_lsscsi(){

    lsscsi --transport 2>/dev/null | while read line
    do
        if [ -n "$(echo $line|grep -i 'cd')" ]
        then
            continue
        fi

        RESULT=$(echo $line | awk '/\/dev/ {print $NF}')
        if [ -n "${RESULT}" ]
        then
            echo $RESULT
        fi
    done
}

###
# Usage: disks_detect_dev
#
# Detect all disks by looking at the /dev/disk/*
# method (failback for lscsci)
###
disks_detect_dev(){
    ##
    return 0
}

###
# Usage: disks_detect [order]
#
# Detect all disk in the system, optional supply
# order, such as: sd,hd
###
disks_detect(){
    DISKORDER=$1
    ALLDISKS=$(disks_detect_lsscsi)

    if [ -z "${ALLDISKS}" ]
    then
        ALLDISKS=$(disks_detect_dev)
    fi

    if [ -z "${ALLDISKS}" ]
    then
        return 1
    fi

    for disk in $DISKORDER
    do
        ## Just to be sure we only have the filename
        DISKNAME=$(basename $disk)
        CONTROLLER=false

        ## Assume i'ts a controller
        if [ ${#DISKNAME} -eq 2 ]
        then
            CONTROLLER=true
        fi

        ## Make sure we order the disks correct based on the length of the string, due to sdaa type of disks
        for udisk in $(echo $ALLDISKS | tr " " "\n" | awk '{ print length(), $1 | "sort" }' | awk '{print $2}')
        do
            ## Check of we already sorted the given udisk
            DONE=$(echo $SDISKS|grep -w $udisk)

            if [ -z "${DONE}" ]
            then
                ## Check if we can find a disk, when it's not a controller match the whole string
                if [ "${CONTROLLER}" == "true" ]
                then
                    found=$(echo $udisk | grep $disk)
                else
                    found=$(echo $udisk | grep -w $disk)
                fi

                ## If found, append to the sorted disk list
                if [ -n "${found}" ]
                then
                    SDISKS="$SDISKS $udisk"
                fi
            fi
        done
    done

    NUMDISKS=0
    for disk in $(echo $SDISKS)
    do
        eval "export DISK${NUMDISKS}=${disk}"
        NUMDISKS=$(( $NUMDISKS + 1 ))
    done

    export NUMDISKS
}
