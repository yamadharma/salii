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
import time
import sys
import subprocess
import hashlib
from shutil import move
from datetime import datetime

from transmission_rpc import Client

from sali.tools import run_command_call
from sali.tools import SimpleLockFile
from sali.tools import ask_question
from sali.exceptions import SaliConfigurationException
from sali.exceptions import SaliImagingException
from sali.exceptions import SaliDataException

class Transmission():

    def __init__(self, cmn):
        self.cmn = cmn
        self.client = Client(
            host=self.cmn.config.get('torrent', 'transmission_host'),
            port=self.cmn.config.getint('torrent', 'transmission_port'),
            username=self.cmn.config.get('torrent', 'transmission_user'),
            password=self.cmn.config.get('torrent', 'transmission_password')
        )

    def get_torrents(self):

        torrents = dict()
        for torrent in self.client.get_torrents():
            torrents[torrent.name] = {
                'data': torrent,
                'id': torrent.id,
                'exists': os.path.isfile(
                    os.path.join(
                        self.cmn.config.get('general', 'torrents_dir'), torrent.name
                    )
                )
            }

        return torrents

    def add_torrent(self, torrent_file_path):
        download_dir = os.path.dirname(torrent_file_path)
        filename = os.path.basename(torrent_file_path)
        torrents = self.get_torrents()

        if filename.rstrip('.torrent') in torrents:
            print('\nRemoving existing torrent from transmission')
            self.client.remove_torrent(torrents[filename.rstrip('.torrent')]['id'])
            time.sleep(5)

        print('\nAdding torrent \'%s\'' % filename)
#        self.client.add_torrent('%s' % torrent_file_path, download_dir=download_dir)
        with open(torrent_file_path, "rb") as f:
            self.client.add_torrent(f, download_dir=download_dir)

class Torrent():

    def __init__(self, cmn):
        self.cmn = cmn
        self.tarball_file_path = os.path.join(
            self.cmn.config.get('general', 'torrents_dir'),
            '%s.tar.%s' % (self.cmn.args.imagename,self.cmn.config.get('torrent', 'compress'))
        )
        self.torrent_file_path = '%s.torrent' % self.tarball_file_path
        self.transmission = Transmission(cmn)

    def file_checksum(self):

        checksum = hashlib.blake2b()
        with open(self.tarball_file_path, 'rb') as fi:
            chunk = fi.read(8192)
            while chunk:
                checksum.update(chunk)
                chunk = fi.read(8192)
        return checksum.hexdigest()

    def check_checksum(self):

        checksum = self.file_checksum()

        if not os.path.isfile('%s.blake2b' % self.tarball_file_path):
            return False

        with open('%s.blake2b' % self.tarball_file_path, 'r') as fi:
            file_checksum = fi.read().strip()

        if checksum != file_checksum:
            return False

        return True

    def create_checksum(self):

        checksum = self.file_checksum()
        with open('%s.blake2b' % self.tarball_file_path, 'w') as fo:
            fo.write(checksum)

    def create_update_torrent(self):

        if ( not os.path.isfile(self.torrent_file_path) or not self.check_checksum() ) or self.cmn.args.force:

            command = [
                self.cmn.config.get('commands', 'transmission-create'), '--private'
            ]
            for tracker in self.cmn.config.get('torrent', 'announce_uri').split(','):
                command.append('--tracker')
                command.append(tracker.strip())
            command.append(
                os.path.basename(self.tarball_file_path)
            )

            rcode = run_command_call(command, cwd=self.cmn.config.get('general', 'torrents_dir'))
            self.create_checksum()
        else:
            print('\nTorrent seems to be up2date, if this is not the case delete checksum file or specify --force')

        self.transmission.add_torrent(self.torrent_file_path)


class TorrentCreateTarball():

    tar_options = ['--preserve-permissions', '--create']

    def __init__(self, cmn):
        self.cmn = cmn
        self.create_torrent = self.cmn.config.image_create_torrent(self.cmn.args.imagename)
        self.tarball_file_path = os.path.join(
            self.cmn.config.get('general', 'torrents_dir'),
            '%s.tar.%s' % (self.cmn.args.imagename,self.cmn.config.get('torrent', 'compress'))
        )

    def create(self):
        if not self.create_torrent:
            raise SaliConfigurationException('torrent=True nog configured for image \'%s\'' % self.cmn.args.imagename)

        command = self.tar_options
        command.insert(0, self.cmn.config.get('commands', 'tar'))

        compress = self.cmn.config.get('torrent', 'compress')
        if compress == 'gz':
            command.append('--gzip')
        elif compress == 'bz2':
            command.append('--bzip2')
        elif compress == 'xz':
            command.append('--use-compress-program=\'xz -T0\'')
        elif compress == 'zst':
            command.append('--use-compress-program=\'zstd -9 -T0 --rsyncable\'')
        else:
            print('\nUncompressed tar')

        if self.cmn.args.verbose:
            command.append('--verbose')


        command.append('--file')
        command.append('%s.tmp' % self.tarball_file_path)
        command.append('.')

        print('\nCreating tarball \'%s\'' % self.tarball_file_path)

        rcode = run_command_call(
            command,
            run_shell=True,
            cwd=os.path.join(
                self.cmn.config.get('general', 'images_dir'),
                self.cmn.args.imagename
            )
        )

        if rcode != 0:
            raise SaliImagingException('Unable to continue, an error has occured')

        move(
            '%s.tmp' % self.tarball_file_path, self.tarball_file_path
        )

def torrent_exists(cmn, torrent_file_path):

    if not os.path.isdir(cmn.config.get('general', 'torrents_dir')):
        raise SaliDataException('Unable to locate directory \'%s\'' %
            cmn.config.get('general', 'torrents_dir')
        )

    if os.path.isfile(torrent_file_path):
        return True

    return False

def maketorrent(cmn):

    tarball = TorrentCreateTarball(cmn)
    torrent = Torrent(cmn)

    print('Welcome to the SALI imager')
    print('   %-20s: %s' % ('imagename', cmn.args.imagename))
    print('   %-20s: %s\n' % ('tarball', tarball.tarball_file_path))

    # First check of the image exists, then ask about it
    if torrent_exists(cmn, tarball.tarball_file_path):
        question = 'Do you want to update existing torrent'
        inform = 'Existing torrent will be updated'
    else:
        question = 'Torrent does not exist, do you want to create it'
        inform = 'A new torrent will be created'

    if cmn.args.yes:
        print(inform, ', you have 5 seconds to ctrl+c')
        time.sleep(5)
    else:
        answer = ask_question(question, true_false=True)

        if not answer:
            print('\nYou answered \'NO\' stopping')
            sys.exit(0)

    lock = SimpleLockFile(cmn)

    if not lock.is_locked:
        lock.lock()

        tarball.create()
        torrent.create_update_torrent()

        lock.unlock()
    else:
        print('\nUnable to fetch/create torrent. Other process is busy or lockfile has not been removed')

def lstorrents(cmn):

    line_format = '%(name)-30s%(sep)s%(exists)-8s%(sep)s%(date_added)-21s%(sep)s%(rate_upload)-13s%(sep)s%(ratio)s'

    print()
    print(
        line_format % {
            'name': ' Name',
            'exists': ' Exists',
            'date_added': ' Date Added',
            'rate_upload': ' Rate Upload',
            'ratio': ' Ratio',
            'sep': '|'
        }
    )
    print(
        line_format % {
            'name': '-' * 30,
            'exists': '-' * 8,
            'date_added': '-' * 21,
            'rate_upload': '-' * 13,
            'ratio': '-' * 6,
            'sep': '+'
        }
    )


    trans = Transmission(cmn)

    for name, torrent in trans.get_torrents().items():
        print(
            line_format % {
                'name': ' ' + name,
                'exists': ' ' + str(torrent['exists']),
                'date_added': datetime.strftime(torrent['data'].date_added, ' %d-%m-%Y %H:%M.%S'),
                'rate_upload': ' ' + str(torrent['data'].rateUpload),
                'ratio': ' ' + str(torrent['data'].ratio),
                'sep': '|'
            }
        )
    print()

def rmtorrent(cmn):

    if cmn.args.yes:
        print('\nRemoving torrent from tranmission, you have 5 seconds to ctrl+c')
        time.sleep(5)
        yes_to_delete = True
    else:
        yes_to_delete = ask_question(
            '\nAre you sure you want remove \'%s\' from tranmission' % cmn.args.torrentname, true_false=True
        )

    if yes_to_delete:
        trans = Transmission(cmn)
        torrents = trans.get_torrents()

        if cmn.args.torrentname not in torrents:
            print('Given torrentname \'%s\' does not exist' % cmn.args.torrentname)

        print('\nRemoving torrent from transmission')
        trans.client.remove_torrent(torrents[cmn.args.torrentname]['id'])

    else:
        print('\nYou answered \'NO\' stopping')
        sys.exit(0)
