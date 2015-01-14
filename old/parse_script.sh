#!/usr/bin/sh

## In this location we will store all installation information
##  partition information, SALI variables, etc
CACHEDIR="/tmp/cache/sali"
if [ ! -d "${CACHEDIR}" ]
then
    mkdir -p $CACHEDIR
fi
VARFILE="${CACHEDIR}/variables"

## Given through cmdline
IMAGESERVER="145.101.32.1"
IMAGENAME="amd64_squeeze_lisa"
PROTOCOL="rsync"

# A simple function which replaces the = with a space
clean_args(){
    echo $@| sed 's/\=/ /g'
}

## Replaces save_variable, load_variable, write_variables
##  it will store the variable name and value to a file
##  and export it to the environment. These variables
##  are always UPPERCASED
#         <name>   <value>
# set_var PROTOCOL rsync
set_var(){
    NAME=$1
    VALUE=$2

    VARFILETMP="${VARFILE}.${$}"

    ## If the file does not exits, create the initial file
    if [ ! -e "${VARFILE}" ]
    then
        echo "CACHEDIR=\"${CACHEDIR}\"" > $VARFILE
        echo "VARFILE=\"${VARFILE}\"" >> $VARFILE
    fi

    ## Check if the given variable already exists in the file
    LINE=$(egrep -n "^${NAME}=" $VARFILE|awk -F: '{print $1}')

    ## Now the store logic
    if [ -n "${LINE}" ]
    then
        sed ''$LINE'd' $VARFILE > $VARFILETMP
        echo "${NAME}=\"${VALUE}\"" >> $VARFILETMP
        mv $VARFILETMP $VARFILE
    else
        echo "${NAME}=\"${VALUE}\"" >> $VARFILE
    fi

    ## Finally export the new variable (or perhaps all!)
}

## This function stores the necessary information
## do fetch the image via bitttorrent
image_torrent(){
    ## If the protcol is not bittorrent then skip the processing
    if [ "${PROTOCOL}" != "bittorrent" ]
    then
        return
    fi

    set $(clean_args $@)

    while [ $# -gt 0 ]
    do
        case "${1}" in
            staging)
                echo "Staging: ${2}"
                shift 2
            ;;
            *)
                shift 1
            ;;
        esac
    done
}

image_rsync(){
    ## If the protocol is not rsync then skip the processing
    if [ "${PROTOCOL}" != "rsync" ]
    then
        return
    fi

    set $(clean_args $@)
    echo "image_rsync $@"
}

disks_detect(){
    set $(clean_args $@)
    echo "disks_detect $@"
}

disks_prep(){
    set $(clean_args $@)
    echo "disks_prep $@"
}

disks_part(){
    set $(clean_args $@)
    echo "disks_part $@"
}

run_script(){
    set $(clean_args $@)
    echo "run_script $@"
}

exception(){
    echo "An error has occured with message:"
    echo " ${@}"
    exit 1
}

check_function_exists(){
    type $@ &>/dev/null
}

salichroot(){
    set $(clean_args $@)
    echo "salichroot $@"
}

set_var TEST aap

. ./master_script

check_function_exists initialize partition
if [ $? -ne 0 ]
then
    exception "Either initialize or partition function could not be located in the master script"
fi

initialize
partition

##
# Run post_installation if function is defined
check_function_exists post_installation
if [ $? -eq 0 ]
then
    post_installation
fi
