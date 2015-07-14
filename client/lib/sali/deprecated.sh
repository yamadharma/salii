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
# Usage: logmsg <message>
#
# Log a message to syslog
###
logmsg(){
    p_comment 10 "$@"
}

###
# Usage: shellout
#
# Opens the console when a error has occurred, ie $COMMAND || shellout
###
shellout() {
    open_console error
}

###
# Usage: write_variables
#
# Writes the variables to an file
###
write_variables() {
    . $SALI_VARIABLES_FILE
    save_variables
}

save_param() {
    ## Just an empty function
    echo
}

###
# Usage: load_variables
#
# Loads the variables
###
load_variables() {
    . $SALI_VARIABLES_FILE
}

variableize_kernel() {
    ## Just an empty function
    echo
}

get_arch() {
    ARCH=`uname -m | sed -e s/i.86/i386/ -e s/sun4u/sparc64/ -e s/arm.*/arm/ -e s/sa110/arm/`
}

adjust_arch(){
    touch /tmp/adjust_arch
}

count_loop(){
    COUNT=$1
    trap 'echo ; echo "Skipping ETHER_SLEEP -> Caught <ctrl>+<c>" ; I=$COUNT' INT
    I=0
    while [ $I -lt $COUNT ]; do
        I=$(( $I + 1 ))
        p_comment 256 "$I "
        sleep 1
    done
    trap INT
}

read_kernel_append_parameters() {
    ## Just an empty function
    echo
}

variableize_kernel_append_parameters() {
    ## Just an empty function
    echo
}

read_local_cfg() {
    ## Just an empty function
    echo
}

p_log() {
    ## Just an empty function
    echo
}

p_whitespace() {
    ## Just an empty function
    echo
}

start_ssh() {
    ## Just an empty function
    echo
}

ping_test() {                                                                             
                                                                                           
    PING_DESTINATION=$1                                                                   
                                                                                           
    PING_RESULT=1                                                                         
                                                                                           
    p_comment 20 "trying to ping your imagserver, ${PING_DESTINATION}"                     
                                                                                           
    # Ping test code submitted by Grant Noruschat <grant@eigen.ee.ualberta.ca>             
    # modified slightly by Brian Finley.                                                   
    PING_COUNT=1                                                                           
    PING_EXIT_STATUS=1                                                                     
    while [ $PING_EXIT_STATUS -ge 0 ]                                                     
    do                                                                                     
                                                                                           
        p_comment 20 "ping attempt ${PING_COUNT}"                                         
        ping -c 1 $PING_DESTINATION > /dev/null 2>&1                                       
        PING_EXIT_STATUS=$?                                                               
                                                                                           
        if [ "$PING_EXIT_STATUS" = "0" ]                                                   
        then                                                                               
                p_comment 20 "we have connectivity to your IMAGESERVER!"                                       
                PING_RESULT=0                                                             
                break                                                                     
        fi                                                                                 
                                                                                           
        PING_COUNT=$(( $PING_COUNT + 1 ))                                                 
        if [ "$PING_COUNT" = "4" ]                                                         
        then                                                                               
                return                                                                     
        fi                                                                                 
                                                                                           
    done                                                                                   
                                                                                               
}

ping_test_imageserver(){
    PING_SERVER=1

    if [ -z "${SALI_IMAGESERVER}" ]
    then
        for file in $(ls -1 /tmp/udhcpc.*)
        do
            . $file
            if [ -n $SALIIMAGESRV ]
            then
                ping_test $SALIIMAGESRV

                if [ $PING_RESULT -eq 0 ]
                then
                    SALI_IMAGESERVER=$SALIIMAGESRV
                    IPADDR=$IPADDR
                    NETMASK=$NETMASK
                    DOMAINNAME=$DOMAINNAME
                    PING_SERVER=0
                    save_variables
                    break
                fi
            fi
        done
    else
        ping_test $SALI_IMAGESERVER
       
        if [ $PING_RESULT -eq 0 ]
        then
            PING_SERVER=0
        fi
    fi
}

do_gateway() {
    add_gateway $1
}

get_base_hostname() {
    hostname -s
}

get_group_name() {
    HOSTNAME=$(hostname -s)
    if [ -f ${SALI_SCRIPTS_DIR}/cluster.txt ]; then
        [ -z "$GROUPNAMES" ] && \
            GROUPNAMES=$(echo $(grep "^${HOSTNAME}:" ${SALI_SCRIPTS_DIR}/cluster.txt | cut -d: -f2 | tr "\n" ' ') | uniq)
        [ -z "$IMAGENAME" ] && \
            IMAGENAME=`grep "^${HOSTNAME}:" ${SALI_SCRIPTS_DIR}/cluster.txt | cut -d: -f3 | grep -v '^[[:space:]]*$' | sed -ne '1p'`
        if [ -z "$GROUP_OVERRIDES" ]; then
            GROUP_OVERRIDES=$(reverse $(echo $(grep "^${HOSTNAME}:" ${SALI_SCRIPTS_DIR}/cluster.txt | cut -d: -f4 | tr "\n" ' ') | uniq))
            # Add the global override on top (least important).
            GROUP_OVERRIDES="`sed -ne 's/^# global_override=:\([^:]*\):$/\1/p' ${SALI_SCRIPTS_DIR}/cluster.txt` $GROUP_OVERRIDES"
        fi
    fi
}
