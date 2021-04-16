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

from configparser import SafeConfigParser
from configparser import ExtendedInterpolation
from logging.config import fileConfig
import logging
import os
import sys

from sali.tools import find_and_add_command, tar_gnu
from sali.exceptions import SaliConfigurationException

# Some defaults that are required, can be overidden in the sali.ini
SALI_CONFIGURATION = {
    'general' : {
        'base_dir'      : '/data/sali',
        'config_dir'    : '${general:base_dir}/config',
        'cache_dir'     : '${general:base_dir}/cache',
        'images_dir'    : '${general:base_dir}/images',
        'torrents_dir'  : '${general:base_dir}/torrents',
        'scripts_dir'   : '${general:base_dir}/scripts',
        'run_dir'       : '${general:base_dir}/run',
        'logfile_config': '${general:cfg_path}/logging.ini',
        'logfile'       : '/var/log/sali.log'
    },
    'rsync' : {
        'target'        : '%(config_dir)s/rsyncd.conf',
        'stubs'         : '%(config_dir)s/rsync_stubs',
    },
    'getimage': {
        'exclude_files': '${general:config_dir}/gi_exclude_files',
        'base_exclude': 'global.excl',
        'default_exclude': 'default.excl'
    },
    'torrent': {
        'transmission_host': '127.0.0.1',
        'transmission_port': 9091,
        'transmission_user': 'transmission',
        'transmission_password': '',
        'announcer': 'local-all:6969'
    },
    'commands': {
        'tar'           : 'tar',
        'rsync'         : 'rsync',
        'ssh'           : 'ssh',
    }
}

class Common():

    def __init__(self, args, cfg_path='/etc/sali'):
        self.args = args
        self.config = Configuration(self.args.config, cfg_path)
        self.__logger = self.get_logger('sali')

    def logger(self, name, type, message):
        types = {
            'debug': self.__logger.debug,
            'info': self.__logger.info,
            'warning': self.__logger.warning,
            'error': self.__logger.error,
            'critical': self.__logger.critical
        }
        if not type in types:
            raise SaliConfigurationException('Given type \'%s\' is not supported in the logger' % type)
        types[type]('%-20s: %s' % (name, message))


    def get_logger(self, name):
        
        fileConfig(
            self.config.get('general', 'logfile_config'), defaults={'logfilename': self.config.get('general', 'logfile')}
        )

        logger = logging.getLogger(name)

        if self.args.verbose or self.args.dry_run:
            logger.setLevel(logging.DEBUG)

        return logger


class Configuration(SafeConfigParser):

    def __init__(self, filename, cfg_path='/etc/sali'):
        if not filename or not os.path.isfile(filename):
            raise SaliConfigurationException('Unable to process configurationfile')

        super().__init__(default_section='general', interpolation=ExtendedInterpolation())

        self.set('general', 'cfg_path', cfg_path)
        self.read(filename)
        self.__validate_configuration()

    def __validate_configuration(self):
        'Validates the configuration and make sure defaults are set'

        for section in SALI_CONFIGURATION:
            # Create the section if it does not exist, but don't do this for the defaultsect
            if not self.has_section(section) and section != self.default_section:
                self.add_section(section)

            # Now check if the variables have a default or not
            for option, value in SALI_CONFIGURATION[section].items():
                if not self.has_option(section, option):
                    self.set(section, option, str(value))
        
        # Find the full-path of the commands
        for command in SALI_CONFIGURATION['commands']:
            find_and_add_command(self, SALI_CONFIGURATION['commands'][command])

        # Check if tar is GNU tar
        tar_gnu(self.get('commands', 'tar'))