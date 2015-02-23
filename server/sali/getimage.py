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
# Copyright 2010-2014 SURFsara

from __future__ import print_function

import os
import sys
import readline
import socket
import tempfile
import time
from stat import ST_ATIME

from sali import tools

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

class GetImage(object):

    block_file_systems = ['ext2', 'ext3', 'ext4', 'jfs', 'xfs', 'vfat', 'fat', 'reiserfs']

    def __init__(self, cmn):
        self.cmn = cmn
        self.logger = self.cmn.get_logger(__name__+'.GetImage')
        self.images_path = os.path.join(self.cmn.cfg.get('general', 'data_dir'), 'images')
        self.image_new = False
        self.getimage_script = None
        self.exclude_file = None

        ## Check if we need to use the interactive mode
        self.golden_client = self.__get_golden_client()
        if not self.golden_client:
            print('Unable to continue failed to resolv golden client hostname', file=sys.stderr)
            sys.exit(1)
        self.image_name = self.__get_image_name()
        if not self.image_name:
            print('Unable to find image', file=sys.stderr)
            sys.exit(1)
        if not os.path.isdir(os.path.join(self.images_path, self.image_name)):
            self.image_new = True

        ## Check if the image is locked
        if tools.img_is_locked(self.cmn, self.image_name):
            print('The image %s is currently locked by the create tarball/torrent process' % self.image_name)
            sys.exit(1)

        ## If not locked, lock it now
        tools.img_lock(self.cmn, self.image_name, 'client::getimage')

        ## Check if we can image
        #if self.image_name in database.Database(self.cmn, 'tarring').get().keys():
        #    print('A tarring process is currently busy with this image, please wait until tarring process is finished')
        #    print('  started at %s' % tarring.get()[self.image_name])
        #    sys.exit(0)

        ## Check for the exlude file, if not given, use the default file, if given and does not exist, exit with an error
        self.custom_exclude_file = self.__get_exclude_file()
        if not self.custom_exclude_file:
            print('Unable to find/locate the exclude file', file=sys.stderr)
            sys.exit(1)
        self.exclude_file = self.__create_exclude_file()

        ## Now ask or start fetch_image
        if not cmn.arguments.yes:
            if self.__yes_no():
                self.__fetch_image()
            else:
                print('You have canceled the getimage procedure')
        else:
            self.__fetch_image()

    def __get_golden_client(self):
        golden_client = None
        self.logger.debug('checking for golden-client argument')
        if not self.cmn.arguments.golden_client:
            self.logger.debug('golden-client argument not found, asking interactive')
            print("\nEnter the golden client address:")
            while not golden_client:
                golden_client = raw_input("  > ")
        else:
            golden_client = self.cmn.arguments.golden_client

        self.logger.debug('trying to resolve golden-client address')
        try:
            rslt = socket.gethostbyaddr(golden_client)
            return golden_client
        except Exception:
            return None

    def __get_image_name(self):
        image_name = None
        self.logger.debug('checking if image argument is set')
        if not self.cmn.arguments.image:
            self.logger.debug('asking for image name interactive')

            readline.set_completer(self.__completer)
            readline.parse_and_bind("tab: complete")

            print("\nEnter the image name (tab completion available):")
            while not image_name:
                image_name = raw_input("  > ")
        else:
            image_name = self.cmn.arguments.image

        return image_name

    def __get_exclude_file(self):
        self.logger.debug('looking for exclude file')        

        exclude_file = None
        if not self.cmn.arguments.exclude:
            if os.path.exists(os.path.join(self.cmn.cfg.get('getimage', 'exclude_files'), self.image_name + '.excl')):
                exclude_file = os.path.join(self.cmn.cfg.get('getimage', 'exclude_files'), self.image_name + '.excl')
            else:
                exclude_file = self.cmn.cfg.get('getimage', 'default_exclude')
        else:
            exclude_file = self.cmn.arguments.exclude

        self.logger.debug('  found file %s' % exclude_file)

        if os.path.exists(exclude_file):
            return exclude_file
        else:
            return None

    def __create_exclude_file(self):
        self.logger.debug('create a exclude_file')

        fd, fname = tempfile.mkstemp(dir=self.cmn.cfg.get('general', 'cache_dir'), text=True)
        fto = os.fdopen(fd, 'w')

        ## Fetch current mount
        self.logger.debug('  fetching current mounts from golden client %s' % self.golden_client)
        fto.write('## ignore all network filesystems and tmpfs mount')
        rcode, stdout, stderr = tools.run_command(self.cmn.cfg.get('commands', 'ssh'), '-x', '-q', self.golden_client, 'mount', shell=False)
        for line in stdout.splitlines():
            if not line.strip():
                continue
            parts = line.strip().split()

            ## ignore all nfs mounted filesystems
            if parts[4] not in self.block_file_systems:
                fto.write(parts[2])

        ## Global exlude file
        self.logger.debug('  using global exclude file')
        fto.write('## global exclude')
        with open(os.path.join(self.cmn.cfg.get('getimage', 'exclude_files'), 'global.excl'), 'r') as fi:
            for line in fi:
                if not line.strip():
                    continue
                fto.write(line.strip()+'\n')

        ## The chosen exclude file
        self.logger.debug('  using exclude file %s' % self.custom_exclude_file)
        fto.write('## chosen exclude file')
        with open(self.custom_exclude_file, 'r') as fi:
            for line in fi:
                if not line.strip():
                    continue
                fto.write(line.strip()+'\n')

        fto.close()
        return fname

    def __completer(self, text, state):
        options = [ x for x in os.listdir(self.images_path) if x.startswith(text) ]
        try:
            return options[state]
        except IndexError:
            return None

    def __del__(self):
        if self.exclude_file and os.path.exists(self.exclude_file):
            self.logger.debug('removing tmpfile %s' % self.exclude_file)
            os.remove(self.exclude_file)

        if self.getimage_script and os.path.exists(self.getimage_script):
            self.logger.debug('removing tmpfile %s' % self.getimage_script)
            os.remove(self.getimage_script)

        if tools.img_is_locked(self.cmn, self.image_name):
            tools.img_unlock(self.cmn, self.image_name)

    def __yes_no(self):

        if self.image_new:
            print("\nWould you like to create a new image '%s' from golden client '%s'" % (self.image_name, self.golden_client))
        else:
            print("\nWould you like to update image '%s' from golden client '%s'" % (self.image_name, self.golden_client))

        answer = None
        while not answer:
            answer = raw_input("  yes or no: ")
            if answer in ['y', 'Y', 'yes', 'Yes', 'YES']:
                return True
            elif answer in ['n', 'N', 'no', 'No', 'NO']:
                return False
            else:
                answer = None
                print('Invalid input, choose y,yes or n,no')

    def __fetch_image(self):
        print("\nFrom:", self.golden_client)
        print("To:", os.path.join(self.images_path, self.image_name))

        fd, fname = tempfile.mkstemp(dir=self.cmn.cfg.get('general', 'cache_dir'), text=True)
        fto = os.fdopen(fd, 'w')
        self.getimage_script = fname
        fbasename = os.path.basename(fname)

        server_ip = list()
        for network, addresses in tools.get_interfaces().items():
            if addresses['ipv4']:
                server_ip.append(addresses['ipv4'])
            if addresses['ipv6']:
                server_ip.append(addresses['ipv6'])

        variables = {
            'rsyncd_sh': '/tmp/' + fbasename + '.sh',
            'rsyncd_cfg': '/tmp/' + fbasename + '.cfg',
            'rsyncd_log': '/tmp/' + fbasename + '.log',
            'server_ip': ", ".join(server_ip),
        }

        fto.write(RSYNCD_SCRIPT % variables)

        fto.close()

        # Send script to remote machine (rsync over ssh)
        #   rsync -e ssh fname client:/tmp/fbasename.sh
        self.logger.debug('copying sali_prepare script to golden client over ssh')
        rcode, stdout, stderr = tools.run_command(
            self.cmn.cfg.get('commands', 'rsync'), '-e', 
            self.cmn.cfg.get('commands', 'ssh'), fname, 
            self.golden_client + ':/tmp/' + fbasename + '.sh', shell=False
        )
        if rcode != 0:
            self.logger.critical('Unable to copy script to golden_client %s over ssh' % self.golden_client)
            sys.exit(1)

        # then run shell script
        self.logger.debug('spawning sali_prepare script on golden client')
        rcode  = tools.run_command_call(
            self.cmn.cfg.get('commands', 'ssh'), '-f', '-x', '-q', self.golden_client, 
            '/bin/sh /tmp/' + fbasename + '.sh &', shell=False
        )

        # Wait for 2 seconds before continuening
        time.sleep(2)

        print('\nRunning rsync')
       
        # make/update the image
        command = [ 
            self.cmn.cfg.get('commands', 'rsync'), 
            '--archive', '--hard-links', '--sparse', 
            '--numeric-ids', '--delete', '--delete-excluded', 
            '--exclude-from=%s' % self.exclude_file, 
            '%s::root/' % self.golden_client, 
            os.path.join(self.images_path, self.image_name) 
        ]

        ## Are we running in verbose mode
        if self.cmn.arguments.verbose:
            command.append('--verbose')

        self.logger.debug('Running command: %s' % ' '.join(command))
       
        rcode = tools.run_command_call(*command, shell=False)
        if rcode != 0:
            self.logger.critical('Unable to run rsync command')
            sys.exit(1)

        time.sleep(2)

        # tell the daemon we are done
        rcode, stdout, stderr = tools.run_command(
            self.cmn.cfg.get('commands', 'rsync'), '%s::__cloning_completed__' % self.golden_client, shell=False
        )

        # Let's update the timestamp
        atime = os.stat(os.path.join(self.images_path, self.image_name))[ST_ATIME]
        os.utime(os.path.join(self.images_path, self.image_name),(atime, time.time()))

        print('Done')
        tools.img_unlock(self.cmn, self.image_name)
        self.__del__()
