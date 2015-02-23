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

from logging import getLogger
from logging import Formatter
from logging import StreamHandler
from logging.handlers import SysLogHandler

from sali import config

class Common(object):
    '''A simple wrapper object to pass options through all layers of SALI'''

    def __init__(self, arguments):
        self.arguments = arguments
        self.cfg = config.Config(self.arguments.config)

    def get_logger(self, name):
        '''Wrapper for the getLogger function'''
       
        address, socktype, level = self.cfg.logging_cfg()
 
        logger = getLogger(name)
        logger.setLevel(level) 

        ## Our main logging handler
        syslog_handler = SysLogHandler(
            address=address,
            facility=SysLogHandler.LOG_DAEMON,
            socktype=socktype
        )
        syslog_handler.setFormatter(
            Formatter('sali [%(levelname)s]: %(name)s - %(message)s')
        )
        logger.addHandler(syslog_handler)

        return logger
