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
# Copyright 2010-2014 SURFsara

###
# $Id$
# $URL$
###

###
# Usage: image_rsync "<RSYNC URL>" [options=""]
#
# This function is part of the initialize and just stores the
# information to the variables file. This information is later
# used to start the installation process
###
image_rsync(){
    if [ "${SALI_PROTOCOL}" != "rsync" ]
    then
        return
    fi

    # Reset the args
    set $(args $@)

    SALI_RSYNC_URL=$1
    shift 1

    while [ $# -gt 0 ]
    do
        case "${1}" in
            options)
                SALI_RSYNC_OPTIONS=$2
                shift 2
            ;;
        esac
    done

    save_variables
}

###
# Usage: image_torrent_url_support "<TORRENT URL>"
#
# A function to test if the given URL for torrent is supported
###
image_torrent_url_support(){
    RESULT=$(echo $1 | egrep "^(rsync|http|https|ftp|tftp)\:\/\/.+$")
    if [ -n "${RESULT}" ]
    then
        return 0
    else
        return 1
    fi
}

###
# Usage: image_rsync "<TORRENT URL>" [staging=""]
#
# This function is part of the initialize and just stores the
# information to the variables file. This information is later
# used to start the installation process
###
image_torrent(){
    if [ "${SALI_PROTOCOL}" != "torrent" ]
    then
        return
    fi

    set $(args $@)

    image_torrent_url_support $1
    if [ $? -ne 0 ]
    then
        exit 1
    fi

    SALI_TORRENT_URL=$1
    shift 1

    while [ $# -gt 0 ]
    do
        case "${1}" in
            staging)
                SALI_STAGING_DIR=$2
                shift 2
            ;;
        esac
    done

    save_variables
}

password(){
    USER=$1
    PASSWORD=$2

    ## Fetch current passwd line use set for easy editing
    set $(egrep "^${USER}" etc/passwd | sed 's/\:/ /g')
    set $1 $PASSWORD $3 $4 $5 $6 $7
    echo $@ | sed 's/ /\:/g'
}
