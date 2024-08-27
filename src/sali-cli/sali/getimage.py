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

import os
import sys
import time

import fasteners

from sali.tools import is_hostname
from sali.tools import ask_question
from sali.exceptions import SaliValidationException
from sali.exceptions import SaliDataException

RSYNCD_SCRIPT = '''
if [ -z "$(pidof rsync)" ]
then
    cat > %(rsyncd_cfg)s << DELIM
list = yes
timeout = 900
dont compress = *.gz *.tgz *.zip *.Z *.ZIP *.bz2 *.deb *.rpm *.dbf *.tar.gz *.tar *.tar.bz2 *.tar.xz *.txz
uid = root
gid = root
hosts allow = %(server_ip)s
hosts deny = *
log file = %(rsyncd_log)s
[root]
 path = /
 exclude = %(rsyncd_cfg)s %(rsyncd_log)s
DELIM
    rsync --daemon --config="%(rsyncd_cfg)s"
    RSYNC_PID=$(pidof rsync)
    tail -f "%(rsyncd_log)s" | while read line
    do
        if [ -n "$(echo $line | grep "__cloning_completed__")" ]
        then
            kill $RSYNC_PID
            break
        fi
    done
    rm -rf "%(rsyncd_cfg)s"
    rm -rf "%(rsyncd_log)s"
    rm -rf "%(rsyncd_sh)s"
else
    rm -rf "%(rsyncd_cfg)s"
    rm -rf "%(rsyncd_sh)s"
    exit 1
fi'''

class GetImage():

    block_file_systems = ['ext2', 'ext3', 'ext4', 'jfs', 'xfs', 'vfat', 'fat', 'reiserfs']
    
    def __init__(self, cmn):
        self.cmn = cmn

    def fetch_image(self):

        ## Steps
        #   - upload script with ssh
        #   - run script with ssh in background
        #   - fetch image from node
        #   - send done command
        pass

def image_exists(cmn):

    if not os.path.isdir(cmn.config.get('general', 'images_dir')):
        raise SaliDataException('Unable to locate directory \'%s\'' % 
            cmn.config.get('general', 'images_dir')
        )

    if os.path.isdir(os.path.join(cmn.config.get('general', 'images_dir'), cmn.args.imagename)):
        return True
    
    return False

def getimage(cmn):
    cmn.logger('sali.getimage.getimage', 'info', 'validate input and create a GetImage class')
    
    print('Welcome to the SALI imager')
    print('   %-20s: %s' % ('golden-client', cmn.args.hostname))
    print('   %-20s: %s' % ('imagename', cmn.args.imagename))

    # First check of the image exists, then ask about it
    if image_exists(cmn):
        question = 'Do you want to update existing image'
        inform = 'Existing image will be updated'
    else:
        question = 'Image does not exist, do you want to create it'
        inform = 'A new image will be created'

    if cmn.args.yes:
        print(inform, ', you have 10 seconds to ctrl+c')
        time.sleep(5)
    else:
        answer = ask_question(question, true_false=True)

        if not answer:
            print('\nYou answered \'NO\' stopping')
            sys.exit(0)

    # Just continue with the class
    lockfile = fasteners.InterProcessLock(
        os.path.join(
            cmn.config.get('general', 'cache_dir'),
            '%s.lock' % cmn.args.imagename
        )
    )
    
    if not lockfile.exists:
        with lockfile:
            gi = GetImage(cmn)
    else:
        print('\nUnable to fetch/create image. Other process is busy or lockfile has not been removed')