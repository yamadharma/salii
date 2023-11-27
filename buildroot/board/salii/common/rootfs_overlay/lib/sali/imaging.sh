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
# Usage: getimage_rsync
#
# Fetch the image via the rsync protocol, is configured by the image_rsync option in
# the master_script
#
###
getimage_rsync(){

    p_service "Fetching image \"${SALI_IMAGENAME}\" via rsync"
    p_comment 10 "url: ${SALI_RSYNC_URL}"
    p_comment 10 "opt: ${SALI_RSYNC_OPTIONS}"

    if [ $(echo "${SALI_RSYNC_OPTIONS}" | head -c 1) != '-' ]
    then
        SALI_RSYNC_OPTIONS_USED="-${SALI_RSYNC_OPTIONS}"
    else
        SALI_RSYNC_OPTIONS_USED="${SALI_RSYNC_OPTIONS}"
    fi

    if [ "${SALI_VERBOSE_LEVEL}" -ge 256 ]
    then
        SALI_RSYNC_OPTIONS_USED="${SALI_RSYNC_OPTIONS_USED}v"
    fi


    /usr/bin/rsync $SALI_RSYNC_OPTIONS_USED --exclude=lost+found/ --exclude=/proc/* --numeric-ids $SALI_RSYNC_URL/ $SALI_TARGET/
    return $?
}

###
# Usage: getimage_transmission_getid <torrent-filename>
#
# Find the torrent-id from transmission-daemon based on the torrent-filename
#
###
getimage_transmission_getid(){
    torrent_name=$(echo $1 | sed 's/.torrent//g')

    result=$(/usr/bin/transmission-remote -l |grep $torrent_name | awk '{print $1}')

    echo $result
}

###
# Usage: getimage_transmission_progress <torrent-id>
#
# Based on the torrent-id in transmission-daemon track the progress of the download
#
###
getimage_transmission_progress(){

    DONE=0

    echo ""

    while [ $DONE -eq 0 ]
    do
        /usr/bin/transmission-remote -t $1 -i > $SALI_CACHE_DIR/torrent_progress

        percent_complete=$(cat $SALI_CACHE_DIR/torrent_progress | awk -F':' '/^\s+Percent\sDone/ {print $NF}' | sed 's/ //g')
        eta=$(cat $SALI_CACHE_DIR/torrent_progress | awk -F':' '/^\s+ETA/ {print $NF}' | sed 's/^ //g')
        have=$(cat $SALI_CACHE_DIR/torrent_progress | awk -F':' '/^\s+Have/ {print $NF}' | sed 's/^ //g')
        total_size=$(cat $SALI_CACHE_DIR/torrent_progress | awk -F':' '/^\s+Total\ssize/ {print $NF}' | sed 's/^ //g')
        download_speed=$(cat $SALI_CACHE_DIR/torrent_progress | awk -F':' '/^\s+Download\sSpeed/ {print $NF}' | sed 's/^ //g')
        upload_speed=$(cat $SALI_CACHE_DIR/torrent_progress | awk -F':' '/^\s+Upload\sSpeed/ {print $NF}' | sed 's/^ //g')

        p_comment 10 "Percent complete: ${percent_complete}"
        p_comment 10 "ETA: ${eta}"
        p_comment 10 "Progress: ${have} / ${total_size}"
        p_comment 10 "Download: ${download_speed} / Upload: ${upload_speed}"
        echo ""

        if [ "$percent_complete" == "100%" ]
        then
            DONE=1
        else
            sleep 15
        fi
    done

}

###
# Usage: getimage_transmission <torrent-filename>
#
# Download the given torrent file via transmission
#
###
getimage_transmission(){

    if [ "${SALI_VERBOSE_LEVEL}" -ge 256 ]
    then
        NO_OUTPUT=">/dev/null 2>&1"
    else
        NO_OUTPUT=""
    fi

    ## Add torrent to download-list
    p_service "Adding torrent-file ${1} to transmission-daemon to ${SALI_TORRENT_STAGING_DIR}"
    /usr/bin/transmission-remote --incomplete-dir $SALI_TORRENT_STAGING_DIR --download-dir $SALI_TORRENT_STAGING_DIR --add $1 $NO_OUTPUT

    ## Get torrent id
    p_comment 10 "Finding torrent-id from transmission-daemon"
    torrent_id=$(getimage_transmission_getid $(basename $1))

    ## Update seed-ratio to always seed
    p_comment 10 "Adjusting seed-ratio to seed always"
    /usr/bin/transmission-remote -t $torrent_id --no-seedratio $NO_OUTPUT

    ## Check for the progress
    getimage_transmission_progress $torrent_id
}

###
# Usage: getimage_torrent
#
# Fetch the image via the torrent protocol, is configured by the image_torrent option in
# the master_script
#
###
getimage_torrent(){

    ## If SALI_TORRENT_STAGING_DIR is not set, give it a default value
    if [ -z "${SALI_TORRENT_STAGING_DIR}" ]
    then
        SALI_TORRENT_STAGING_DIR="${SALI_TARGET}/tmp"
    fi
    save_variables

    ## Say hello
    p_service "Fetching image via torrent"
    p_comment 10 "url: ${SALI_TORRENT_URL}"

    ## Check if we need to download the torrent via rsync, or we can specify it as a url
    torrent_filename=$(download_file "${SALI_TORRENT_URL}")

    ## Based on the backend, use that option
    case "${SALI_TORRENT_BACKEND}" in
        transmission)
            p_comment 10 "using transmission"
            getimage_transmission $torrent_filename
        ;;
    esac

    ## Based on the verbose mode show the extraction
    if [ "${SALI_VERBOSE_LEVEL}" -ge 256 ]
    then
        tar_opts="-pxvf --numeric-owner"
    else
        tar_opts="-pxvf --numeric-owner"
    fi

    ## We need to remove the .torrent from the filename
    SALI_TARBALL="$(echo $torrent_filename|sed 's/.torrent//g')"
    SALI_TARBALL="${SALI_TORRENT_STAGING_DIR}/$(basename $SALI_TARBALL)"

    ## Change our dir to where we must unpack
    cd $SALI_TARGET

    ## Unpack
    case "${SALI_TARBALL}" in
        *.tar.gz)
            zcat "${SALI_TARBALL}" | tar $tar_opts -
        ;;
        *.tar)
            tar $tar_opts "${SALI_TARBALL}"
        ;;
        *)
            p_comment 10 "Unsupport file-format ${SALI_TARBALL}"
            return 1
        ;;
    esac

    if [ $? -ne 0 ]
    then
        p_comment 10 "An error has occured"
        return 1
    fi

    p_section "Finished installing node"
}
