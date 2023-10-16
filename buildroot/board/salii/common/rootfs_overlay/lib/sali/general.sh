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
    logger -t section "${TEXT}" 

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
    SEP_STR=""
    for char in $(seq 1 $COLS)
    do
        SEP_STR="${SEP_STR}${SEP}"
    done
    printf "%s\n" "${SEP_STR}"
}

###
# Usage: p_stage "<line of text>"
#
# Print a line of text to indicate a stage
###
p_stage(){
    logger -t stage "${1}" 
    printf "\n> %s\n" "${1}"
}

###
# Usage: p_service "<line of text>"
#
# Print a line of text to show the progress within a stage
###
p_service(){
    logger -t service "${1}"
    printf "  :: %s\n" "${1}"
}

###
# Usage: p_comment "<line of text>"
#
# Print a line of text to add some more context to the current stage
###
p_comment(){
    logger -t comment "${2}"
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
        return 1
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
# Usage: open_console <error|error_startup>
#
# Open a login session
###
open_console(){

    ## Check if we must supply additional info
    case "${1}" in
        error_startup)
            echo
            p_section "Startup error"
            echo
            cat $SALI_ERROR_STARTUP_FILE
        ;;
        error)
            echo
            p_section "Installation error"
            echo
            cat $SALI_ERROR_FILE
        ;;
        *)
            echo
            p_section "Console mode"
            echo
            cat $SALI_CONSOLE_FILE
        ;;
    esac

    echo
    exec /bin/cttyhack /bin/login -f root 
}

###
# Usage: download_file "<URL>"
#
# This function downloads the file to the cache dir
###
download_file(){
    FILENAME=$(basename "${1}")
    case "$(echo $1 | awk -F':' '{print $1}')" in
        http|https|ftp)
            if [ "$(is_yes $SALI_SSL_VALID)" -eq 0 ]
            then
                CURL_ARGS="--insecure --connect-timeout 10"
            else
                CURL_ARGS="--connect-timeout 10"
            fi

            curl $CURL_ARGS --silent --output $SALI_CACHE_DIR/$FILENAME $1 &>/dev/null
            
        ;;
        tftp)
            p_comment 0 "TFTP is not supported yet"
        ;;
        rsync)
            rsync -azz $1 $SALI_CACHE_DIR/$FILENAME &>/dev/null
        ;;
        *)
            p_comment 0 "Unsupported protocol found please use http,https,ftp,tftp or rsync"
            return 1
        ;;
    esac

    if [ -e "${SALI_CACHE_DIR}/${FILENAME}" ]
    then
        echo "${SALI_CACHE_DIR}/${FILENAME}"
    else
        return 1
    fi
}
