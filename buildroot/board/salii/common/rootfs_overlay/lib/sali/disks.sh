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
# Usage: disks_detect_lscsi
#
# Detect all disks using the lsscsi command
###
disks_detect_lsscsi(){

    ## First all the "normal" disks, due to some limitations for some nvme disks
    lsscsi --transport --no-nvme 2>/dev/null | while read line
    do
        if [ -n "$(echo $line|grep -i ' cd ')" ]
        then
            continue
        fi

        RESULT=$(echo $line | awk '/\/dev/ {print $NF}')
        if [ -n "${RESULT}" ]
        then
            echo $RESULT
        fi
    done

    nvme list --output-format=json 2>/dev/null | jq -r '.Devices[].DevicePath' | while read line
    do
        echo $line
    done

}

###
# Usage: disks_detect_dev
#
# Detect all disks by looking at the /dev/disk/*
# method (fallback for lscsci)
###
disks_detect_dev(){

    DISKS=""

    ## Loop trough all possible /dev/disks/*/*
    for disk_by in $(ls -1 /dev/disk/)
    do
        ## Just to be sure the location exists
        if [ -e "/dev/disk/${disk_by}" ]
        then
            ## Then find all disks (not the actual partitions)
            for disk in $(ls -1 /dev/disk/$disk_by | grep -v part)
            do
                ## Use realpath to find out the /dev/* device
                real_disk=$(realpath /dev/disk/$disk_by/$disk)

                ## Only interested in the disk name, not the partition
                case "$(basename $real_disk)" in
                    nvme*)
                         real_disk=$(echo $real_disk|sed -r 's/p[0-9]+$//g')
                    ;;
                    *)
                         real_disk=$(echo $real_disk|sed -r 's/[0-9]+$//g')
                    ;;
                esac

                ## Is it realy a disk?
                if [ -n "$(cat /proc/partitions | grep $(basename $real_disk))" ]
                then
                    match=$(echo $DISKS | grep -c $real_disk)
                    case "${match}" in
                        0)
                            DISKS="${DISKS}${real_disk} "
                            echo $real_disk
                        ;;
                    esac
                fi
            done
        fi
    done
}

###
# Usage: disks_detect [order]
#
# Detect all disk in the system, optional supply
# order, such as: sd,hd
###
disks_detect(){
    DISKORDER=$@
    ALLDISKS=$(disks_detect_lsscsi)

    if [ -z "${ALLDISKS}" ]
    then
        ALLDISKS=$(disks_detect_dev)
    fi

    if [ -z "${ALLDISKS}" ]
    then
        return 1
    fi

    SDISKS=""
    for disk in $DISKORDER
    do
        ## Just to be sure we only have the filename
        DISKNAME=$(basename $disk)
        CONTROLLER=false

	    case "${DISKNAME}" in
            nvme*)
                if [ ${#DISKNAME} -eq 4 ]
                then
                    CONTROLLER=true
                fi
            ;;
            sd*|hd*)
                ## Assume i'ts a controller
                if [ ${#DISKNAME} -eq 2 ]
                then
                    CONTROLLER=true
                fi
            ;;
            *)
                p_comment 10 "Given disk prefix ${DISKNAME} is not supported, skipping"
                continue
            ;;
        esac

        ## Make sure we order the disks correct based on the length of the string, due to sdaa type of disks
        for udisk in $(echo $ALLDISKS | tr " " "\n" | awk '{ print length(), $1 | "sort" }' | awk '{print $2}')
        do
            ## Check of we already sorted the given udisk
            DONE=$(echo $SDISKS|grep -w $udisk)

            if [ -z "${DONE}" ]
            then
                ## Check if we can find a disk, when it's not a controller match the whole string
                if [ "${CONTROLLER}" == "true" ]
                then
                    found=$(echo $udisk | grep $disk)
                else
                    found=$(echo $udisk | grep -w $disk)
                fi

                ## If found, append to the sorted disk list
                if [ -n "${found}" ]
                then
                    SDISKS="$SDISKS $udisk"
                fi
            fi
        done
    done

    NUMDISKS=0
    for disk in $(echo $SDISKS)
    do
        eval "DISK${NUMDISKS}=${disk}"
        NUMDISKS=$(( $NUMDISKS + 1 ))
    done

    ## Instead of exporting, use the save_variables fucntion
    save_variables
}

###
# Usage: disks_prep <msdos|gpt> <disk> [disks]
#
# Prepare the disks for repartition for msdos or gpt layout

###
disks_prep(){
    LABEL=$1
    shift 1
    
    case "${1}" in
        all)
            ## We need some global variables
            . $SALI_VARIABLES_FILE
            for disknum in $(seq 0 $((NUMDISKS-1)))
            do
                eval d_name="\${DISK${disknum}}"
                DISKS="${DISKS}${d_name} "
            done
        ;;
        *)
            DISKS=$@
        ;;
    esac

    p_service "Preparing disk(s)"

    for disk in $DISKS
    do
        sgdisk --zap-all $disk >/dev/null 2>&1
        partprobe $disk >/dev/null 2>&1

        if [ $SALI_VERBOSE_LEVEL -ge 10 ]
        then
            p_comment 10 "/usr/sbin/parted -s -- ${disk} mklabel ${LABEL}"
        else
            p_comment 0 "setting disklabel ${LABEL} for ${disk}"
        fi

        if [ $SALI_VERBOSE_LEVEL -ge 256 ]
        then
            /usr/sbin/parted -s -- $disk mklabel $LABEL
        else
            /usr/sbin/parted -s -- $disk mklabel $LABEL >/dev/null 2>&1
        fi

        sleep 2
        partprobe $disk >/dev/null 2>&1
    done
}

###
# Usage: disks_last_size <disk>
#
# Get the last size in MiB of the disk
#
# Syntax required options:
#  disk       : specify the disk you wan't to edit
#
###
disks_last_size(){
    DISK=$1

    if [ -b "${DISK}" ]
    then
        LAST_SIZE=$(/usr/sbin/parted -s -- $DISK unit MiB print free | tail -n2 | awk '/Free Space/ {print $1}' | sed 's/MiB//g' | awk -F. '{print $1}')
        if [ -n "${LAST_SIZE}" ]
        then
            if [ -n "$(echo $LAST_SIZE|egrep "[0-9\.]+")" ]
            then
                echo $(echo "$LAST_SIZE + 1" | bc)
                return 0
            elif [ -n "$(echo $LAST_SIZE|grep kB)" ]
            then
                echo 0
                return 0
            fi
        fi
    fi

    return 1
}

###
# Usage: disks_cerate_partition <disk> <size> <type> [flag]
#
# Get the last size in MiB of the disk
#
# Syntax required options:
#  disk       : specify the disk you wan't to edit
#
###
disks_create_partition(){
    ## We need to fetch the DISK label every time, because this could be changes per disk!
    DISK_LABEL=$(/usr/sbin/parted -s -- "${1}" print 2>/dev/null | awk '/Partition Table/ {print $NF}')
    LAST_SIZE=$(disks_last_size $1)

    case "${2}" in
        -1|100%)
            END_SIZE="-1"
        ;;
        *)
            END_SIZE=$(echo "$LAST_SIZE + $2" | bc )
        ;;
    esac


    case "${DISK_LABEL}" in
        gpt)
            p_comment 10 "/usr/sbin/parted -s -- ${1} mkpart primary ${LAST_SIZE}MiB ${END_SIZE}MiB"
            /usr/sbin/parted -s -- "${1}" mkpart primary "${LAST_SIZE}MiB" "${END_SIZE}MiB"
        ;;
        ## Yes I know there is some redunand code between msdos and gpt, but this make it more readable
        msdos)
            PART_NUM=$(/usr/sbin/parted -s -- "${1}" print 2>/dev/null | awk '/^ [0-9].*/ {print $1}' | tail -n1)
            if [ -z "${PART_NUM}" ]
            then
                PART_NUM=0
            fi

            if [ $PART_NUM -eq 3 ]
            then
                p_comment 10 "/usr/sbin/parted -s -- ${1} mkpart extended ${LAST_SIZE}MiB -1"
                /usr/sbin/parted -s -- "${1}" mkpart extended "${LAST_SIZE}MiB" -1
                PART_NUM=$(/usr/sbin/parted -s -- "${1}" print 2>/dev/null | awk '/^ [0-9].*/ {print $1}' | tail -n1)
                EXTENDED_LAST_SIZE=$LAST_SIZE
            fi

            if [ $PART_NUM -ge 3 ]
            then
                case "${2}" in
                    -1|100%)
                        END_SIZE="-1"
                    ;;
                    *)
                        END_SIZE=$(echo "$EXTENDED_LAST_SIZE + $2" | bc )
                    ;;
                esac
                p_comment 10 "/usr/sbin/parted -s -- ${1} mkpart logical ${EXTENDED_LAST_SIZE}MiB ${END_SIZE}MiB"
                /usr/sbin/parted -s -- "${1}" mkpart logical "${EXTENDED_LAST_SIZE}MiB" "${END_SIZE}MiB"
                EXTENDED_LAST_SIZE=$END_SIZE
            else
                p_comment 10 "/usr/sbin/parted -s -- ${1} mkpart primary ${LAST_SIZE}MiB ${END_SIZE}MiB"
                /usr/sbin/parted -s -- "${1}" mkpart primary "${LAST_SIZE}MiB" "${END_SIZE}MiB"
            fi
        ;;
    esac
        

    if [ "${3}" != "none" ]
    then
        echo $3 | sed 's/,/\n/g' | while read disk_flag
        do
            PART_NUM=$(/usr/sbin/parted -s -- "${1}" print 2>/dev/null | awk '/^ [0-9].*/ {print $1}' | tail -n1)
            p_comment 10 "/usr/sbin/parted -s -- ${1} set ${PART_NUM} ${disk_flag} on"
            /usr/sbin/parted -s -- "${1}" set "${PART_NUM}" "${disk_flag}" on
        done
    fi
}

###
# Usage: disks_format <disk> <type>
#
# Create partitions on specific disks
#
# Syntax required options:
#  disk       : specify the disk you wan't to edit
#  type       : filesystem type
#
# Syntax optional options:
#  label=boot                           the label of the partition
#  options="-I 128"                     check the man page mkfs.<fstype> for the options
#
###
disks_format(){
    DISK=$1
    TYPE=$2
    LABEL=$(echo $3|awk -F'=' '{print $NF}')
    shift 3
    OPTIONS=$(echo $@|awk -F'=' '{print $NF}')

    if [ -n "${LABEL}" ]
    then
        case "${TYPE}" in
            vfat)
                LABEL="-n ${LABEL}"
            ;;
            *)
                LABEL="-L ${LABEL}"
            ;;
        esac
    fi

    if [ "$SALI_VERBOSE_LEVEL" -ne 256 ]
    then
        QUIET="-q"
    else
        QUIET=""
    fi

    case "${TYPE}" in
        ext2)
            p_comment 10 "/usr/sbin/mkfs.ext2 ${DISK} ${LABEL} ${OPTIONS}"
            /sbin/mkfs.ext2 -F $DISK $LABEL $OPTIONS $QUIET
        ;;
        ext3)
            p_comment 10 "/usr/sbin/mkfs.ext3 ${DISK} ${LABEL} ${OPTIONS}"
            /sbin/mkfs.ext3 -F $DISK $LABEL $OPTIONS $QUIET
        ;;
        ext4)
            p_comment 10 "/usr/sbin/mkfs.ext4 ${DISK} ${LABEL} ${OPTIONS}"
            /sbin/mkfs.ext4 -F $DISK $LABEL $OPTIONS $QUIET
        ;;
        xfs)
            p_comment 10 "/sbin/mkfs.xfs ${DISK} ${LABEL} ${OPTIONS}"
            /sbin/mkfs.xfs $DISK -f $LABEL $OPTIONS $QUIET
        ;;
        vfat)
            # Note: We only allow creation of Fat32, should already be the default size
            # but just to make it more explicit
            p_comment 10 "/sbin/mkfs.vfat -F32 ${DISK} ${LABEL} ${OPTIONS}"
            if [ "$SALI_VERBOSE_LEVEL" -ne 256 ]
            then
                /sbin/mkfs.vfat ${DISK} -F32 ${LABEL} ${OPTIONS} >/dev/null 2>&1
            else
                /sbin/mkfs.vfat ${DISK} -F32 ${LABEL} ${OPTIONS}
            fi
        ;;
        swap)
            p_comment 10 "/sbin/mkswap ${DISK} ${LABEL} ${OPTIONS}"
            if [ "$SALI_VERBOSE_LEVEL" -ne 256 ]
            then
                /sbin/mkswap $DISK $LABEL $OPTIONS >/dev/null 2>&1
            else
                /sbin/mkswap $DISK $LABEL $OPTIONS
            fi
        ;;
    esac
}


###
# Usage: disks_part <disk> <mountpoint> <size> [options]
#
# Create partitions on specific disks
#
# Syntax required options:
#  disk       : specify the disk you wan't to edit
#  mountpoint : /<path>, swap, none, raid.<id>, pv.<id>
#  size       : specify size in MiB (-1 means rest of disk)
#
# Syntax optional options:
#  type=<ext2|ext3|ext4|xfs|swap>       currently supported filesystems
#  flag=<bios_grub|lvm|raid|boot|esp>   which flag must be set on the partition
#                                       when using raid.<id> or lvm.<id> the flag
#                                       lvm or raid is optional!, you can specify multiple
#                                       flags by separating with ,
#  label=boot                           the label of the partition
#  options="-I 128"                     check the man page mkfs.<fstype> for the options
#  dirperms=1777                        with which permissions must the mount directory be
#
###
disks_part() {
    set $(args $@)

    unset LABEL OPTIONS DIRPERMS ARGS

    TYPE=none
    FLAG=none
   
    IN_OPTIONS=0 
    DISK=$1
    MOUNTPOINT=$2
    SIZE=$3
    shift 3

    while [ $# -gt 0 ]
    do
        case "${1}" in
            type)
                TYPE="${2}"
                IN_OPTIONS=0
                shift 2
            ;;
            flag)
                FLAG="${2}"
                IN_OPTIONS=0
                shift 2
            ;;
            label)
                LABEL="${2}"
                IN_OPTIONS=0
                shift 2
            ;;
            options)
                OPTIONS="${2}"
                IN_OPTIONS=1
                shift 2
            ;;
            dirperms)
                DIRPERMS="${2}"
                IN_OPTIONS=0
                shift 2
            ;;
            *)
                if [ $IN_OPTIONS -eq 1 ]
                then
                    OPTIONS="${OPTIONS} ${1}"
                else
                    ARGS="${ARGS}${1} "
                fi
                shift 1
            ;;
        esac
    done

    ### Check if given label is supported, else show error
    echo $FLAG | sed 's/,/\n/g' | while read disk_flag
    do
        case "${disk_flag}" in
            boot|swap|bios_grub|esp|none)
                ## Ok let's go
            ;;
            lvm|raid)
                p_comment 0 "Currently lvm|raid are not supported yet"
            ;;
            *)
                p_comment 0 "Given flag ${FLAG} is not supported (bios_grub|lvm|raid|none)"
                open_console error
            ;;
        esac
    done

    p_service "Creating partition on disk ${DISK} with size ${SIZE}, type ${TYPE}, mountpoint ${MOUNTPOINT}"
    disks_create_partition $DISK $SIZE $FLAG
    PART_NUM=$(/usr/sbin/parted -s -- "${DISK}" print | awk '/^ [0-9].*/ {print $1}' | tail -n1)

    ## Just wait a couple of sec and also force partprobe
    sleep 2
    partprobe $DISK >/dev/null 2>&1

    case "$(basename $DISK)" in
        nvme*)
            PART_PREFIX="p"
        ;;
        *)
            PART_PREFIX=""
        ;;
    esac

    ## And again just wait, don't care about the speed
    sleep 2

    ## Check if given filesystem is supported, else show error
    case "${TYPE}" in
        ext2|ext3|ext4|xfs|swap|vfat|none)
            disks_format "${DISK}${PART_PREFIX}${PART_NUM}" "${TYPE}" "label=${LABEL}" "options=${OPTIONS}"
        ;;
        *)
            p_comment 0 "Given filesystem type ${TYPE} is not supported (ext2|ext3|ext4|xfs|swap)"
            open_console error
        ;;
    esac

    ## For verbose logging
    for var in FLAG LABEL OPTIONS DIRPERMS
    do
        eval var_value="\${${var}}"
        if [ -n "${var_value}" ]
        then
            p_comment 10 "$(echo $var | tr '[:upper:]' '[:lower:]'): ${var_value}"
        fi
    done

    echo "$MOUNTPOINT ${DISK} $TYPE $DIRPERMS" >> $SALI_CACHE_DIR/mounts
}

###
# Usage: disks_mount
#
# Mount the partitioned disks on a specific target (default /target)
#
# Syntax optional options:
#  target=/target           Specify on which root directory the partitions must be mounted
#                           default is $SALI_TARGET     
###
disks_mount() {
    TARGET=$1

    ## Make sure we have a default value
    if [ -z "${TARGET}" ]
    then
        TARGET=$SALI_TARGET
    fi

    ## Loop trough the supported file-systems
    cat $SALI_CACHE_DIR/mounts | egrep 'ext[0-9]|xfs|vfat' | sort | while read path disk type dirperms
    do
        mount_path="${TARGET}${path}"
        p_service "Mounting ${disk} with type ${type} on ${mount_path}"

        ## Check if target exists, if not run mkdir
        if [ ! -d "${mount_path}" ]
        then
            p_comment 10 "Creating folder ${mount_path}"
            if [ -n "${dirperms}" ]
            then
                mkdir -m $dirperms -p $mount_path
            else
                mkdir -p $mount_path
            fi
        fi

        p_comment 10 "/bin/mount $disk -t $type $mount_path"
        /bin/mount $disk -t $type $mount_path
    done
}
