#!/bin/sh

TARGETDIR=$1
TMPDIR=$(realpath "${TARGETDIR}/../build/linux_firmware")
FIRMWARE_DIR=${TARGET_DIR}/lib/firmware
MODULES_DIR=${TARGET_DIR}/lib/modules
MODINFO=$(which modinfo)
GIT=$(which git)
GIT_URL=http://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git

clone_repository(){
    $GIT clone $GIT_URL $TMPDIR
}

if [ ! -d "${TMPDIR}" ]
then
    clone_repository
else
    cd $TMPDIR && git pull
    if [ $? -ne 0 ]
    then
        rm -rf $TMPDIR
        clone_repository
    fi
fi

for module in $(find "${MODULES_DIR}" -name "*.ko" -type f)
do
    for firmware in $($MODINFO $module | awk '/^firmware/ {print $2}')
    do
        if [ ! -f "${FIRMWARE_DIR}/${firmware}" ]
        then
            LOCATION=$(dirname "${FIRMWARE_DIR}/${firmware}")
            if [ ! -d "${LOCATION}" ]
            then
                mkdir -p "${LOCATION}"
            fi

            if [ -f "${TMPDIR}/${firmware}" ]
            then
                cp -a "${TMPDIR}/${firmware}" "${FIRMWARE_DIR}/${firmware}"
            fi
        fi
    done
done
