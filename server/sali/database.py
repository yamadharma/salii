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
import gdbm

import sqlite3

class Database_old(object):

    __shared_state = dict()

    def __init__(self, cmn, name):
        self.__dict__ = self.__shared_state
        self.cmn = cmn
        self.name = name

    def get(self):
        if not hasattr(self, '__db'):
            self.__db = shelve.Shelf(gdbm.open(os.path.join(self.cmn.cfg.get('general', 'cache_dir'), self.name +'.db'), 'n'))
        return self.__db

    def close(self):
        if not hasattr(self, '__db'):
            return 0
        self.__db.close()
        del self.__db

class Database(object):
    
    def __init__(self, cmn, name):
        pass
