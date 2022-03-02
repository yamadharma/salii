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
import json

from sali.tools import find_command
from sali.tools import run_command
from sali.exceptions import SaliValidationException

def rsyncconfig(cmn):
    base_dir = cmn.config.get('general', 'images_dir')
    template_data = {
        'sali_scripts_dir': cmn.config.get('general', 'scripts_dir'),
        'sali_torrents_dir': cmn.config.get('general', 'torrents_dir'),
        'rsyncd_sali_images': ''
    }

    for item in sorted(os.listdir(base_dir)):
        template_data['rsyncd_sali_images'] += '[%s]\n   path=%s\n' % (
            item, os.path.join(base_dir, item)
        )

    with open(cmn.config.get('rsync', 'template')) as fi:
        new_data = fi.read() % template_data

    with open(cmn.config.get('rsync', 'target'), 'w') as fo:
        fo.write(new_data)

    print('\nRsync config has been updated')

def transmissionconfig(cmn):
    transmission_cfg = '/etc/transmission-daemon/settings.json'
    transmission_daemon = find_command('transmission-daemon')

    if not os.path.isfile(transmission_cfg) or not transmission_daemon:
        raise SaliValidationException('unable to generate transmission-daemon config, seems not to be installed')

    rcode, stdout, stderr = run_command([
        cmn.config.get('commands', 'pidof'),
        transmission_daemon
    ])

    if rcode == 0:
        raise SaliValidationException('unable to save configuration, stop transmission-daemon first!')

    with open(transmission_cfg, 'r') as fi:
        transmission_json = json.load(fi)

    data_to_set = {
        "download-dir": cmn.config.get('general', 'torrents_dir'),
        "incomplete-dir": cmn.config.get('general', 'torrents_dir'),
        "rpc-authentication-required": True,
        "rpc-bind-address": "127.0.0.1",
        "rpc-port": 9091,
        "rpc-username": cmn.config.get('torrent', 'transmission_user'),
        "rpc-password": cmn.config.get('torrent', 'transmission_password'),
        "rpc-enabled": True,
    }

    save_json = False
    for key, value in data_to_set.items():
        if key in transmission_json:
            if value != transmission_json[key]:
                save_json = True
                transmission_json[key] = value

    if save_json:
        with open(transmission_cfg, 'w') as fo:
            json.dump(transmission_json, fo, indent=4)
