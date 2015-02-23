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
disks_detect_lscsi(){
    ##
    return 0
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

    ALLDISKS=$(disks_detect_lscsi)

    if [ -z "${ALLDISKS}" ]
    then
        ALLDISKS=$(disks_detect_dev)
    fi

    if [ -z "${ALLDISKS}" ]
    then
        return 1
    fi

    echo $ALLDISKS
}
