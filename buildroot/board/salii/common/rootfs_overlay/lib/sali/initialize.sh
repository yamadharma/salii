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

    if [ -z $SALI_RSYNC_OPTIONS ]
    then
        SALI_RSYNC_OPTIONS=-aHS
    fi

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
                SALI_TORRENT_STAGING_DIR=$2
                shift 2
            ;;
        esac
    done

    save_variables
}

###
# Usage: password <UID> <PWD>
#
# This will change the password for a given user
# if the user does not exist, it will be created
###
password(){
    USER=$1
    PASSWORD=$2

    p_comment 0 "REMARK: We recommend to use function authorized_keys instead of using passwords"

    MOD_USER=$(egrep "^${USER}" /etc/passwd)
    if [ -n "${MOD_USER}" ]
    then
        p_comment 0 "Changing password for user ${USER}"
        ## Fetch current passwd line use set for easy editing
        set $(egrep "^${USER}" /etc/passwd | sed 's/\:/ /g')

        ## Create a tmp file excluding the user we want to edit
        egrep -v "^${USER}" /etc/passwd > /tmp/passwd2
        echo $1 $PASSWORD $3 $4 $5 $6 $7 | sed 's/ /\:/g' >> /tmp/passwd2
        mv /tmp/passwd2 /etc/passwd
    else
        p_comment 0 "Adding user ${USER}"
        ## Get the latest UID number and add 1
        NUM=$(cat /etc/passwd | awk -F':' '{print $3}' | sort | tail -n 1)
        NUM=$(($NUM+1))
        echo "${USER}:${PASSWORD}:${NUM}:0:root:/tmp:/bin/bash" >> /etc/passwd
    fi
}
