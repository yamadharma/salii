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
}

variableize_kernel_append_parameters() {
    ## Just an empty function
}

read_local_cfg() {
    ## Just an empty function
}
