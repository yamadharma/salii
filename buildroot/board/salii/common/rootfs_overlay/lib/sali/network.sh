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
# Usage: do_ifup <interface>
#
#  A wraper for the ifup command, depending on the verbose
#  level stdout and stderr will be redirected to /dev/null
###
do_ifup(){
    if [ "${SALI_VERBOSE_LEVEL}" -ge 256 ]
    then
        /sbin/ifup $1
    else
        /sbin/ifup $1 2>&1 > /dev/null
    fi
}

###
# Usage: default_gateway <ip address>
#
#  Use this default gw
###
add_gateway(){
    if [ "${SALI_VERBOSE_LEVEL}" -ge 256 ]
    then
        /sbin/route add default gw $1
    else
        /sbin/route add default gw $1 2>&1 > /dev/null
    fi
}

###
# Usage: add_interface <interface> <dhcp|static> [<address> <netmask>]
#
#  Add the interface to the interfaces file, so we can use ifup, ifdown
###
add_interface(){

    case "${2}" in 
        dhcp)
            /bin/cat >> $SALI_INTERFACES_FILE << EOF
auto ${1}
iface ${1} inet dhcp

EOF
        ;;
        static)
            ## When we use static we expect arguments $3 (ip) and $4 (netmask)
            if [ -z "${3}" -a -z "${4}" ]
            then
                return 1
            fi
            /bin/cat >> $SALI_INTERFACES_FILE << EOF
auto ${1}
iface ${1} inet static
    address ${3}
    netmask ${4}

EOF
        ;;
        *)
            ## Invalid given method, so return 1
            return 1
        ;;
    esac
}
