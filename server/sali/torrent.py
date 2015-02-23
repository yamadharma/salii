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

# Based on the code of py3createtorrent by Robert Nitsch
#    http://www.robertnitsch.de/projects/py3createtorrent

import hashlib
import os
import time
import re

from sali.bencode import bencode
from sali import exceptions
from sali import release
from sali import tools

## Some default sizes
## KB   = Kilobyte = 1000 Bytes
## KIB  = Kibibyte = 1024 Bytes <-- The real size!
KIB = 2**10
MIB = KIB * KIB

def sha1_20(data):
    '''Return the first 20 bytes of the givens data's SHA1 hash'''
    m = hashlib.sha1()
    m.update(data)
    return m.digest()[:20]

class CreateTorrent(object):

    def __init__(self, cmn, torrent_file):
        self.cmn           = cmn
        self.torrent_file  = torrent_file

        if not self.cmn.cfg.has_section('imager') and not self.cmn.cfg.has_option('imager', 'announce'):
            raise exceptions.SaliConfigurationException('Could not locate configuration option imager.announce')

        if os.path.isfile(torrent_file):
            self.torrent_announce   = self.__get_announce_list()
            self.torrent_size       = os.path.getsize(self.torrent_file)
            self.torrent_location   = os.path.dirname(self.torrent_file)
            self.torrent_name       = os.path.basename(self.torrent_file)
        else:
            raise exceptions.SaliTorrentException('class CreateTorrent support only single files!')

        self.torrent_piece_length = self.__get_piece_length()
        self.torrent_store = os.path.join(self.torrent_location, self.torrent_name + '.torrent')

    def __get_announce_list(self):
        base_regex = r'.+\:\/\/(?P<ip>%s)\:[0-9]+\/.+'

        server_list = list()
        add_ip4, add_ip6 = False, False
        for server in self.cmn.cfg.get('imager', 'announce').split(','):
            ## ipv4 check
            if re.search(base_regex % '0\.0\.0\.0', server):
                add_ip4 = server
            ## ipv6 check
            elif re.search(base_regex % '0\:0\:0\:0\:0\:0\:0\:0|\:\:'):
                add_ip6 = server
            else:
                server_list.append(server)

        if add_ip4 or add_ip6:
            interfaces = tools.get_interfaces()
            for interface, address in interfaces.items():
                if add_ip4 and address.has_key('ipv4') and address['ipv4']:
                    server = re.sub('0\.0\.0\.0', address['ipv4'], add_ip4)
                    if server not in server_list:
                        server_list.append(server)

                if add_ip6 and address.has_key('ipv6') and address['ipv6']:
                    server = re.sub('(0\:0\:0\:0\:0\:0\:0\:0|\:\:)', address['ipv4'], add_ip4)
                    if server not in server_list:
                        server_list.append(server)
        return server_list

    def __get_piece_length(self):

        if self.torrent_size < 0:
            raise ValueError('size must be greater than 0')

        if self.torrent_size < 16 * KIB:
            return 16 * KIB

        piece_length = 256 * KIB

        while self.torrent_size / piece_length > 2000:
            piece_length *= 2        

        while self.torrent_size / piece_length < 8:
            piece_length /= 2

        # Ensure that 16 KIB <= piece_length <= 1 * MIB
        piece_length = max(min(piece_length, 1 * MIB), 16 * KIB)

        return int(piece_length)

    def __get_single_fileinfo(self):
        
        ## Intialize some vars
        length = 0
        pieces = bytearray()
        md5    = hashlib.md5()

        ## open the file as binary!
        with open(self.torrent_file, 'rb') as fh:
            while True:
                piece_data = fh.read(self.torrent_piece_length)

                _len = len(piece_data)
                if _len == 0:
                    break

                md5.update(piece_data)
                length += _len
                pieces += sha1_20(piece_data)

        return {
            'pieces':   pieces,
            'name':     self.torrent_name,
            'length':   length,
            'md5sum':   md5.hexdigest(),
        }

    def write_torrent(self):

        metainfo = dict()
        metainfo['creation date']   = int(time.time())
        metainfo['created by']      = 'SALI %s' % release.version
        metainfo['announce']        = self.torrent_announce[0]
        if len(self.torrent_announce) > 1:
            ## A bit confusing, but the it's a list in a list
            metainfo['announce-list'] = [self.torrent_announce]
        metainfo['comment']         = 'This is image %s' % self.torrent_name

        if os.path.isfile(self.torrent_file):
            metainfo['info'] = self.__get_single_fileinfo()

        if len(metainfo['info']['pieces']) % 20 != 0:
            raise exceptions.SaliTorrentException('amount of torrent pieces is not a multiple of 20')
        metainfo['info']['piece length']    = self.torrent_piece_length
        metainfo['info']['private']         = 1
        metainfo['info']['name']            = self.torrent_name

        with open(self.torrent_store, 'wb') as fh:
            fh.write(bencode(metainfo))
