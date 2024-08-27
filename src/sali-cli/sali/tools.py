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
import re
import subprocess
import socket
import ipaddress
import getpass
import sys
from collections import namedtuple

import netifaces

from sali.exceptions import SaliConfigurationException

def version_info(major, minor, micro, releaselevel='alpha', serial=0):
    'Just to generate a Python like hex version'

    level_hex = { 'alpha': 'a', 'beta':  'b','final': 'f', }

    if releaselevel in level_hex:
        rl = level_hex[releaselevel]
    else:
        rl = 'a'

    VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')
    vi          = VersionInfo(major=major, minor=minor, micro=micro, releaselevel=releaselevel, serial=serial)

    _hexstring = '0x%02d%02d%02d%s%d' % (
        major, minor, micro, rl, serial
    )
    return int(_hexstring, 16), vi

def is_executable(filename):

    if os.path.exists(filename) and os.access(filename, os.X_OK):
        return True
    
    return False


def find_command(command):

    for path in os.environ.get('PATH').split(os.pathsep):
        cmd = os.path.join(path, command)
        if is_executable(cmd):
            return cmd

    return None

def find_and_add_command(cfg, command, required=True):
    'A script to find a specific command, when required is True and command is not found, exit'

    if is_executable(command):
        cfg.set('commands', os.path.basename(command), command)
    else:
        found = find_command(command)
        if not found:
            raise SaliConfigurationException('Unable to found full-path of command \'%s\'' % command)
        cfg.set('commands', command, found)

def tar_gnu(command):
    'Function to check if we have gnu tar'

    p = subprocess.Popen(
        [command, '--version'], stdout=subprocess.PIPE
    )
    stdout, stderr = p.communicate()

    if not re.search(r'tar \(GNU tar\)', stdout.decode('utf-8').strip(), re.MULTILINE):
        raise SaliConfigurationException('Tar command \'%s\' does not seem to be GNU tar' % command)


def is_hostname(name):

    try:
        ipaddress.ip_address(name)
        raise ValueError("Only hostname is allowed, found %s" % name)
    except ValueError:
        pass

    try:
        socket.gethostbyname(name)
    except socket.gaierror:
        return False
    
    return True

def ask_question(question, default=None, true_false=False, r_type=str, password=False):

    if password:
        a_input = getpass.getpass
    else:
        a_input = input

    did_not_answer_counter = 0

    while True:

        if not default and not true_false:
            answer = a_input('%s: ' % (question))
        elif true_false:
            answer = a_input('%s <y|n>: ' % (question))
        else:
            answer = a_input('%s [%s]: ' % (question, default))

        if not answer and default:
            answer = default

        if answer:
            try:
                if true_false:
                    if answer in ['y', 'Y', 'yes', 'YES']:
                        return True
                    else:
                        return False
                else:
                    return r_type(answer)
            except ValueError:
                answer = None
                print('Given value for question does not match the type needed: %s' % r_type.__name__)

        did_not_answer_counter += 1
        if did_not_answer_counter > 5:
            print('I give up, please do not bash me to much!!!', file=sys.stderr)
            sys.exit(1)

def get_interfaces(skip=['lo']):

    ## Store here the interfaces, ip6 still needs some work
    ip4_interfaces = dict()
    ip6_interfaces = dict()

    ## Loop trough the interfaces, skip the skip
    for intf in netifaces.interfaces():
        if intf in skip:
            continue

        addresses = netifaces.ifaddresses(intf)

        if netifaces.AF_INET in addresses:
            ip4_interfaces[intf] = list()
            for addr in addresses[netifaces.AF_INET]:
                ip4_interfaces[intf].append(addr['addr'])
        
        if netifaces.AF_INET6 in addresses:
            ip6_interfaces[intf] = list()
            for addr in addresses[netifaces.AF_INET6]:
                ip6_interfaces[intf].append(addr['addr'])

    return ip4_interfaces, ip6_interfaces

def get_dictionary_values(dictionary):

    if isinstance(dictionary, dict):
        for values in dictionary.values():
            yield from get_dictionary_values(values)
    elif isinstance(dictionary, list):
        for values in dictionary:
            yield from get_dictionary_values(values)
    else:
        yield dictionary

def run_command(args, run_shell=False, cwd=None):

    if run_shell:
        args = " ".join(args)

    if cwd:
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, shell=run_shell)
    else:
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=run_shell)
    stdout, stderr = p.communicate()

    return p.returncode, stdout, stderr

def run_command_call(args, run_shell=False, cwd=None):

    if run_shell:
        args = " ".join(args)

    if cwd:
        return subprocess.call(args, shell=run_shell, cwd=cwd)
    else:
        return subprocess.call(args, shell=run_shell)

class SimpleLockFile():

    def __init__(self, cmn):
        self.lock_file_path = os.path.join(cmn.config.get('general', 'cache_dir'), '%s.lock' % cmn.args.imagename)

        if not os.path.exists(cmn.config.get('general', 'cache_dir')):
            os.makedirs(cmn.config.get('general', 'cache_dir'))

        if os.path.exists(self.lock_file_path):
            self.is_locked = True
        else:
            self.is_locked = False

    def lock(self):
        with open(self.lock_file_path, 'w') as fi:
            fi.write('Locked by process %d\n' % os.getpid())

    def unlock(self):
        if os.path.exists(self.lock_file_path):
            os.remove(self.lock_file_path)
