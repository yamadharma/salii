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

import os
import shelve
import cPickle
import binascii

import lmdb

class Database(object):
    
    def __init__(self, cmn, name):
        self.db_path = os.path.join(
            cmn.cfg.get('general', 'cache_dir'), name
        )
        self.env = lmdb.open(self.db_path, max_dbs=2)

    def write(self, key, data):
        with self.env.begin(write=True) as txn:
            txn.put(key, cPickle.dumps(data))

    def get(self, key):
        with self.env.begin(write=False) as txn:
            try:
                return cPickle.loads(txn.get(key))
            except TypeError:
                return None

    def getall(self):
        outlist = list()
        with self.env.begin(write=False) as txn:
            for key, data in iter(txn.cursor()):
                outlist.append({'info_hash': binascii.hexlify(key), 'peer_info': cPickle.loads(data)})
        return outlist

    def sync(self):
        self.env.sync()
