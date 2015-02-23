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

# This code is based on the code written by Sreejith Kesavan
#   https://github.com/semk/Pytt

import httplib
from socket import inet_aton
from struct import pack

from tornado import web

from sali import bencode
from sali.server.web import base

INVALID_REQUEST_TYPE = 100
MISSING_INFO_HASH = 101
MISSING_PEER_ID = 102
MISSING_PORT = 103
INVALID_INFO_HASH = 150
INVALID_PEER_ID = 151
INVALID_NUMWANT = 152
GENERIC_ERROR = 900 

class StatsHandler(web.RequestHandler):
    pass

class AnnounceHandler(base.SaliRequestHandler):

    def __store_peer_info(self, info_hash, peer_id, ip, port, status):

        peer_info = self.db.get(info_hash)
        if peer_info:
            if (peer_id, ip, port, status) not in peer_info:
                peer_info.append((peer_id, ip, port, status))
        else:
            peer_info = [(peer_id, ip, port, status)]

        self.db.write(info_hash, peer_info)
        self.db.sync()

    def __count_clients(self, info_hash, state):
        count = 0
        peer_info = self.db.get(info_hash)

        if peer_info:
            for pi in peer_info:
                if pi[3] == state:
                    count += 1
        return count

    def __get_peer_list(self, info_hash, numwant, compact, no_peer_id):

        peer_info = self.db.get(info_hash)
        if compact:
            byteswant = numwant * 6
            compact_peers = ''
            
            if peer_info:
                for pi in peer_info:
                    ip = inet_aton(pi[1])
                    port = pack('>H', int(pi[2]))
                    compact_peers += (ip+port)
            return compact_peers[:byteswant]
        else:
            peers = list()
            if peer_info:
                for pi in peer_info:
                    p = dict()
                    p['peer_id'], p['ip'], p['port'], rest = pi
                    if no_peer_id:
                        del p['peer_id']
                    peers.append(p)
            return peers[:numwant]

    def get(self):

        ## These are the required parameters we need
        info_hash   = self.get_argument('info_hash')
        peer_id     = self.get_argument('peer_id')
        ip          = self.request.remote_ip
        port        = self.get_argument('port')

        if not info_hash:
            return self.send_error(MISSING_INFO_HASH)
        if not peer_id:
            return self.send_error(MISSING_PEER_ID)
        if not port:
            return self.send_error(MISSING_PORT)

        if len(info_hash) != self.cmn.cfg.getint('web', 'info_hash_len'):
            print(len(info_hash))
            return self.send_error(INVALID_INFO_HASH)
        if len(peer_id) != self.cmn.cfg.getint('web', 'peer_id_len'):
            print(len(peer_id))
            return self.send_error(INVALID_PEER_ID)

        ## These are the optional parameters
        uploaded    = int(self.get_argument('uploaded', 0))
        downloaded  = int(self.get_argument('downloaded', 0))
        left        = int(self.get_argument('left', 0))
        compact     = int(self.get_argument('compact', 0))
        no_peer_id  = int(self.get_argument('no_peer_id', 0))
        event       = self.get_argument('event', '')
        numwant     = int(self.get_argument('numwant', self.cmn.cfg.get('web', 'default_allowed_peers')))
        if numwant > self.cmn.cfg.get('web', 'max_allowed_peers'):
            self.send_error(INVALID_NUMWANT)

        ## What todo whit these?
        key         = self.get_argument('key', '')
        tracker_id  = self.get_argument('trackerid', '')

        if event:
            self.__store_peer_info(info_hash, peer_id, ip, port, event)

        response = {}
        response['interval']        = self.cmn.cfg.get('web', 'interval')
        response['min interval']    = self.cmn.cfg.get('web', 'min_interval')
        response['tracker id']      = tracker_id
        response['complete']        = self.__count_clients(info_hash, 'completed')
        response['incomplete']      = self.__count_clients(info_hash, 'started')
        response['peers']           = self.__get_peer_list(info_hash, numwant, compact, no_peer_id)

        self.set_header('Content-type', 'text/plain')
        self.write(bencode.bencode(response))

class ScrapeHandler(web.RequestHandler):

    def get(self):
        pass
