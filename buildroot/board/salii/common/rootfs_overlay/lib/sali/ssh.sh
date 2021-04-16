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
# Copyright 2010-2021 SURFsara

###
# Usage: ssh_gen_key <type> <target>
#
# Wrapper for creating ssh keys
###
ssh_gen_key(){
    if [ "${SALI_VERBOSE_LEVEL}" -ge 256 ]
    then
        ssh-keygen -t $1 -N "" -f $2
    else
        ssh-keygen -t $1 -N "" -f $2 -q
    fi
}

###
# Usage: ssh_authorized_key <username> <pubkey>
#
# Saves the ssh pub key for a given user
###
ssh_authorized_key(){
    ## Check if user exists
    USER=$(egrep "^${1}" /etc/passwd) 
    if [ -z "${USER}" ]
    then
        p_comment 0 "User ${1} does not exist, not saving ssh pubkey"
    else
        HOMEDIR=$(echo $USER|awk -F':' '{print $6}')
        if [ ! -d "${HOMEDIR}/.ssh" ]
        then
            mkdir -p "${HOMEDIR}/.ssh"
        fi

        echo $2 > "${HOMEDIR}/.ssh/authorized_keys"
        chown $1 "${HOMEDIR}/.ssh/authorized_keys"
        chmod 600 "${HOMEDIR}/.ssh/authorized_keys"
    fi
}
