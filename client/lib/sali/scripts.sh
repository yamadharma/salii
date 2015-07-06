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
# Usage: fetch_scripts <url>
#
# This will fetch the needed post and pre install scripts
###
fetch_scripts(){
    LOCATION=$(download_file $1)

    if [ ! -d ${SALI_SCRIPTS_DIR} ]
    then
        echo 1
    fi

    chown -R root:root $SALI_SCRIPTS_DIR

    echo 0
}

###
# Usage: run_script <command> [chroot=<yes|no>] [args]
#
# Run a pre or post install script, by default the script is not run
# in a chroot env.
###
run_script(){
    ## reset the args
    set $(args $@)

    SCRIPT=$1
    shift 1

    ARGS=""

    while [ $# -gt 0 ]
    do
        case "${1}" in
            chroot)
                if [ $(is_yes $2) -eq 0 ]
                then
                    CHROOT=yes
                fi
                shift 2
            ;;
            *)
                ARGS="${ARGS} ${1}"
                shift 1
            ;;
        esac
    done

    p_service "Running script ${SALI_SCRIPTS_DIR}/${SCRIPT}"

    $SALI_SCRIPTS_DIR/$SCRIPT $ARGS
}
