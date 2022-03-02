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

import os
import sys
import time
import tempfile
import re
from stat import ST_ATIME
from stat import ST_MTIME
from threading import Thread
from datetime import datetime

import paramiko

from sali.tools import is_hostname
from sali.tools import ask_question
from sali.tools import get_interfaces
from sali.tools import get_dictionary_values
from sali.tools import run_command_call
from sali.tools import run_command
from sali.tools import SimpleLockFile
from sali.exceptions import SaliValidationException
from sali.exceptions import SaliDataException
from sali.exceptions import SaliImagingException

class GetImageExclude():

    sali_rsync_exclude = tempfile.NamedTemporaryFile(mode='w+t', prefix='sali-rsync-exclude')
    extend_re = re.compile(r'^#extends\:(?P<file>.+)')

    def __init__(self, cmn, exclude_file_systems=list()):
        self.cmn = cmn
        self.exclude_file_systems = exclude_file_systems

    def __fetch_exclude_data(self, exclude_file):
        lines = list()

        ## Check if we have a extends
        has_extends = self.extend_re.search(
            open(exclude_file).readline().strip()
        )
        if has_extends:
            base_exclude_file = os.path.join(
                self.cmn.config.get('getimage', 'exclude_files'),
                has_extends.group('file')
            )
            lines += self.__fetch_exclude_data(base_exclude_file)

        with open(exclude_file, 'r') as fi:
            for line in fi:
                if not line.strip() or line.strip().startswith('#'):
                    continue
                if line.strip() not in lines:
                    lines.append(line.strip())

        return lines

    def get_exclude_file(self):

        ## Check if we have a specific exclude file for the image, of not take the default
        exclude_file = os.path.join(
            self.cmn.config.get('getimage', 'exclude_files'),
            self.cmn.args.imagename
        )

        if not os.path.exists(exclude_file):
            exclude_file = os.path.join(
                self.cmn.config.get('getimage', 'exclude_files'),
                self.cmn.config.get('getimage', 'default_exclude')
            )

            if not os.path.exists(exclude_file):
                raise SaliValidationException('Unable to locate rsync exclude file \'%s\'' % exclude_file)

        exclude_data = self.__fetch_exclude_data(exclude_file)
        if self.exclude_file_systems:
            exclude_data += self.exclude_file_systems

        for excl in exclude_data:
            self.sali_rsync_exclude.write('%s\n' % excl)
        self.sali_rsync_exclude.flush()

        return self.sali_rsync_exclude.name

class GetImage():

    sali_prep_file = tempfile.NamedTemporaryFile(mode='w+t', prefix='sali-prepare-', suffix='.sh')
    block_file_systems = ['ext2', 'ext3', 'ext4', 'jfs', 'xfs', 'vfat', 'fat', 'reiserfs']
    taropts = [ '-p', '-c', '-f' ]
    ssh_client = None
    
    def __init__(self, cmn):
        self.cmn = cmn

        ## Create an upload remote script
        self.__create_remote_script()
        self.__ssh_upload_remote_script()
        exclude_file_systems = self.__ssh_exclude_filesystems()
        self.rsync_exclude_file = GetImageExclude(cmn, exclude_file_systems)

    def __create_remote_script(self):

        net4, net6 = get_interfaces()
        interfaces = list(get_dictionary_values(net4))
        
        variables = {
            'rsyncd_path': '/tmp',
            'rsyncd_basename': os.path.basename(self.sali_prep_file.name),
            'server_ip': ','.join(interfaces)
        }

        with open(os.path.join(self.cmn.config.get('general', 'config_dir'), 'sali-prepare.template')) as fi:
            for line in fi:
                self.sali_prep_file.write(
                    (line % variables)
                )
        self.sali_prep_file.flush()

    def __ssh_exclude_filesystems(self):
        if not self.ssh_client:
            self.ssh_client = self.__get_ssh_client()

        stdin, stdout, stderr = self.ssh_client.exec_command('mount')
        exclude_fs = list()

        if stdout.channel.recv_exit_status() == 0:
            for line in stdout.readlines():
                if not line.strip():
                    continue
                parts = line.strip().split()
                if parts[4] not in self.block_file_systems:
                    exclude_fs.append(
                        parts[2] + '/*'
                    )

        return exclude_fs

    def __ssh_upload_remote_script(self):
        if not self.ssh_client:
            self.ssh_client = self.__get_ssh_client()
        sftp_client = self.ssh_client.open_sftp()
        sftp_client.put(
            self.sali_prep_file.name, 
            '/tmp/%s' % os.path.basename(self.sali_prep_file.name)
        )
        sftp_client.close()

    def __ssh_run_remote_script(self):
        if not self.ssh_client:
            self.ssh_client = self.__get_ssh_client()
        
        print('\nSpawning ssh session with sali-prepare script')
        stdin, stdout, stderr = self.ssh_client.exec_command(
            "bash /tmp/%s" % os.path.basename(self.sali_prep_file.name)
        )

        ## Wait until it stops!
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                stdoutlines = stdout.readlines()

        return True

    def __get_ssh_client(self):
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.load_system_host_keys()
            ssh_client.connect(
                hostname=self.cmn.args.hostname, 
                username=self.cmn.config.get('getimage', 'username')
            )
            return ssh_client
        except paramiko.ssh_exception.SSHException as error:
            raise SaliImagingException("ssh %s" % error)

    def fetch_image(self):

        ## Fire the sali-prepare script in a thread
        background_process = Thread(target=self.__ssh_run_remote_script)
        background_process.start()
        time.sleep(2)

        ## Fetch the image
        command = [
            self.cmn.config.get('commands', 'rsync'),
            '--archive', '--hard-links', '--sparse',
            '--numeric-ids', '--delete', '--delete-excluded', 
            '--exclude-from', self.rsync_exclude_file.get_exclude_file(),
            '%s::root/' % self.cmn.args.hostname,
            os.path.join(
                self.cmn.config.get('general', 'images_dir'),
                self.cmn.args.imagename
            )
        ]

        if self.cmn.args.verbose:
            command.append('--verbose')

        print('\nFetching image with rsync')
        rcode = run_command_call(command, run_shell=False)
        if rcode != 0:
            raise SaliDataException('Failed to fetch image with rsync')

        ## Send done command and wait for sali-prepare to stop
        print('\nSending done signal to sali-prepare script\n')
        rcode, stdout, stderr = run_command([
            self.cmn.config.get('commands', 'rsync'),
            '%s::__cloning_completed__' % self.cmn.args.hostname
        ])

        ## Update the timestamp on the target imagedir
        atime = os.stat(
            os.path.join(
                self.cmn.config.get('general', 'images_dir'),
                self.cmn.args.imagename
            )
        )[ST_ATIME]
        os.utime(
            os.path.join(
                self.cmn.config.get('general', 'images_dir'),
                self.cmn.args.imagename
            ),
            (atime, time.time())
        )

        while background_process.is_alive():
            print('Waiting to ssh session to close')
            time.sleep(2)

        if self.cmn.config.image_create_torrent(self.cmn.args.imagename):
            print('\nTo make a torrent please run the following command:')
            print('    - %s maketorrent %s\n' % (os.path.basename(sys.argv[0]), self.cmn.args.imagename))

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
    print('   %-20s: %s\n' % ('imagename', cmn.args.imagename))

    # First check of the image exists, then ask about it
    if image_exists(cmn):
        question = 'Do you want to update existing image'
        inform = 'Existing image will be updated'
    else:
        question = 'Image does not exist, do you want to create it'
        inform = 'A new image will be created'

    if cmn.args.yes:
        print(inform, ', you have 5 seconds to ctrl+c')
        time.sleep(5)
    else:
        answer = ask_question(question, true_false=True)

        if not answer:
            print('\nYou answered \'NO\' stopping')
            sys.exit(0)

    lock = SimpleLockFile(cmn)

    if lock.is_locked and not cmn.args.force:
        print('\nUnable to fetch/create image. Other process is busy or lockfile has not been removed')
        return

    if lock.is_locked and cmn.args.force:
        print('\nArgument -f/--force has been set, ignoring lockfile. You have 10 seconds to cancel.')
        time.sleep(10)

    # When all is ok, lock, get and unlock
    lock.lock()
    gi = GetImage(cmn)
    gi.fetch_image()
    lock.unlock()

def lsimages(cmn):
    base_dir = cmn.config.get('general', 'images_dir')

    line_format = '%-30s%s%s'

    print()
    print( line_format % ('Imagename', '|', ' Modified time'))
    print(
        line_format % (
            '-' * 30, '+', '-' * 20
        )
    )
    for item in sorted(os.listdir(base_dir)):
        if not os.path.isdir(os.path.join(base_dir, item)):
            continue
        date = datetime.fromtimestamp(
            os.stat(os.path.join(base_dir, item))[ST_MTIME]
        )

        print(
            line_format % (
                item, '|', datetime.strftime(date, ' %d-%m-%Y %H:%M.%S')
            )
        )
    print()
