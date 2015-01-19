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
# Usage: check_function_exists <function1> [<function2>...]
#
# Checks if a given function exists
#
# Example:
#
# check_function_exists initialize partition
# if [ $? -ne 0 ]
# then
#     echo "Could not find (all) required functions"
#     exit 1
# fi
###
check_function_exists(){
    type $@ &>/dev/null
}

###
# Usage: args type=ext2
#
# Replaces a = with a space
###
args(){
    echo $@| sed 's/\=/ /g'
}

### 
# Usage: p_section "<line of text>"
#
# Print the given line of text centered in the console between
# [ and ]
###
p_section(){
    TEXT=$1

    ## Fetch the width of the console, minus 2 and minus the TEXT length
    TEXT_LEN=$(printf "$TEXT" | wc -L)
    COLS=$((($(stty size | awk '{print $2}') - 2 ) - $TEXT_LEN))

    ## If the amount of COLS is greater than LENGTH center the text
    if [ $COLS -ge $TEXT_LEN ]
    then
        LEFT=$(($COLS / 2))
        RIGHT=$(($COLS - $LEFT))
        LINE="[$(printf "%*s%s%*s" $LEFT "" "${TEXT}" $RIGHT "")]"
    else
        printf "[ %s ]" "${TEXT}"
    fi
    
    printf "${LINE}\n"
}

###
# Usage: p_header
#
# Prints a nice header, uses the p_section command
###
p_header(){
    p_section "Welcome to SALI ${SALI_VERSION}"
    p_section "https://oss.trac.surfsara.nl/sali"
}

###
# Usage: p_separator [character]
#
# Prints a separater at the max width of the console
###
p_separator(){
    if [ -z "${1}" ]
    then
        SEP="-"
    else
        SEP=$1
    fi

    COLS=$(stty size | awk '{print $2}')
    for char in $(seq 1 $COLS)
    do
        printf "${SEP}"
    done
    printf "\n"
}

###
# Usage: p_stage "<line of text>"
#
# Print a line of text to indicate a stage
###
p_stage(){
    printf "\n> %s\n" "${1}"
}

###
# Usage: p_service "<line of text>"
#
# Print a line of text to show the progress within a stage
###
p_service(){
    printf "  :: %s\n" "${1}"
}

p_comment(){
    if [ $SALI_VERBOSE_LEVEL -ge $1 ]
    then
        printf "    . %s\n" "${2}"
    fi
}

###
# Usage: supported_script "<path to script>"
#
# Checks of the master script is supported by this version of SALI
###
supported_script(){
    FIRSTLINE=$(head -n 1 $1)

    if [ -z "$(echo $FIRSTLINE | awk '/(SALI\:)(2|2\.0)$/ {print $2}')" ]
    then
        echo "Supplied masterscript is not supported by this version of SALI!"
        echo "  this SALI version supports script versions: SALI:2, SALI:2.0"
        exit 1
    fi
}

###
# Usage: is_yes <variable>
#
# A simple wrapper script to determinine when a variable is y|yes|Y|Yes|YES|1|True
#  return 0 for false or 1 for true
###
is_yes(){
    case "${1}" in
        y|Y|yes|YES|Yes|True|true|TRUE|1)
            echo 1
        ;;
        *)
            echo 0
        ;;
    esac
}

###
# Usage: open_console
#
# Open a login session
###
open_console(){
    echo
    exec /bin/cttyhack /bin/login -f root 
}
