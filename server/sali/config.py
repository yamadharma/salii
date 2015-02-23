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
import ConfigParser
import sys
from logging.handlers import SYSLOG_UDP_PORT
from socket import SOCK_DGRAM
from socket import SOCK_STREAM

## Set the defaults from DEFAULT to general
ConfigParser.DEFAULTSECT = 'general'

## This is the base configuration of SALI every required option must be
## specified here
SALI_CONFIGURATION = {
    'general' : {
        'config_dir'    : '/etc/sali',
        'data_dir'      : '/data/sali',
        'cache_dir'     : '/var/cache/sali',
        'run_dir'       : '/run/sali',
    },
    'logging' : {
        'level'      : 10,
        'socktype'   : 'udp',
        'address'    : '/dev/log'
    },
    'rsync' : {
        'target'        : '%(config_dir)s/rsyncd.conf',
        'stubs'         : '%(config_dir)s/rsync_stubs',
    },
    'daemons' : {
        'web'           : True,
        'imager'        : True,
    },
    'web' : {
        'listen'        : '0.0.0.0',
        'port'          : 8080,
        'templates'     : '%(config_dir)s/html',
        'http_static'   : '%(config_dir)s/html/static',
        'info_hash_len' : 20,
        'peer_id_len'   : 20,
        'max_allowed_peers': 55,
        'default_allowed_peers': 50,
        'interval'      : 5,
        'min_interval'  : 1,
    },
    'imager' : {
        'images'        : '',
        'compress'      : True,
        'sleep'         : 300,
        'announce'      : 'http://0.0.0.0:8080/announce',
    },
    'commands': {
        'tar'           : 'tar',
        'rsync'         : 'rsync',
        'ssh'           : 'ssh',
    },
    'getimage' : {
        'default_exclude'   : '%(config_dir)s/exclude_files/default.excl',
        'exclude_files'     : '%(config_dir)s/exclude_files', 
    }
}

class Config(ConfigParser.SafeConfigParser):
    '''Our Config class, it's is a wrapper around the ConfigParser.SafeConfigParser'''

    def __init__(self, config_file=None):

        ## Keep the filename for references when we want to display error messages
        self.config_file = config_file

        ## Intialize the base class
        ConfigParser.SafeConfigParser.__init__(self)

        ## Load when possible the configuration from file
        if config_file and os.path.isfile(config_file):
            self.read([config_file,])

        ## Validate the config, check if all options in SALI_CONFIGURATION are set
        self.__validate_configuration()

    def __validate_configuration(self):
        '''Validates the given configuration, if option is not specified then use the default option'''

        for section in SALI_CONFIGURATION:
            ## Check if the required section exists, create when not (except for DEFAULTSECT!)
            if not self.has_section(section) and section != ConfigParser.DEFAULTSECT:
                self.add_section(section)

            ## Now check the options whithin a section
            for option, value in SALI_CONFIGURATION[section].items():
                if not self.has_option(section, option):
                    self.set(section, option, str(value))

    def logging_cfg(self):
        
        try:
            level = self.getint('logging', 'level')
        except ValueError:
            print('Critical error has occured, logging.level must be a integer', file=sys.stderr)
            sys.exit(1)

        address = self.get('logging', 'address')
        if not os.path.exists(address):
            address = address.split(':')
            if len(address) > 2 or len(address) < 1:
                print('Critical error has occured, logging.address must be <address>[:<port>] format', file=sys.stderr)
                sys.exit(1)
            elif len(address) == 1:
                address = (address[0], SYSLOG_UDP_PORT)

        if self.get('logging', 'socktype') not in ['tcp', 'udp']:
            print('Critical error has occured, logging.sdocktype must be udp or tcp', file=sys.stderr)
            sys.exit(1)
        socktype = {
            'tcp': SOCK_STREAM,
            'udp': SOCK_DGRAM,
        }[self.get('logging', 'socktype')]

        return address, socktype, level
