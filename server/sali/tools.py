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

import sys
import os
import subprocess
import re
from collections import namedtuple

def _print(*args, **kwargs):
    print(*args, **kwargs)

def create_daemon(workdir, umask, default_max_fd=1024):
    '''http://code.activestate.com/recipes/278731/'''

    if (hasattr(os, "devnull")):
        redirect_to = os.devnull
    else:
        redirect_to = "/dev/null"

    try:
        pid = os.fork()
    except OSError as err:
        raise Exception('Unable to fork process: %s', err.strerror)

    if(pid == 0):
        os.setsid()

        try:
            pid = os.fork()
        except OSError as err:
            raise Exception('Unable to fork second process: %s'. err.strerror)

        if(pid == 0):
            os.chdir(workdir)
            os.umask(umask)
        else:
            os._exit(0)
    else:
        os._exit(0)

    import resource
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
        maxfd = default_max_fd

    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:
            pass
    os.open(redirect_to, os.O_RDWR)
    os.dup2(0, 1)
    os.dup2(0, 2)

    return 0

def get_uptime():
    if os.path.isfile('/proc/uptime'):
        with open('/proc/uptime', 'r') as fh:
            uptime_seconds = float(fh.readline().split()[0])
            days, remainder = divmod(float(uptime_seconds), 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days == 1:
                return '%d day, %02d:%02d' % (days, hours, minutes)
            elif days > 1:
                return '%d days, %02d:%02d' % (days, hours, minutes)
            else:
                return '%02d:%02d' % (hours, minutes)
    else:
        return 'Unsupported OS'

def find_command(command=None):

    ## Auto find the command by using the PATH
    fullcmd = None
    for path in os.environ.get('PATH').split(os.pathsep):
        cmdpath = os.path.join(path, command)
        if os.path.exists(cmdpath) and os.access(cmdpath, os.X_OK):
            fullcmd = cmdpath
            break

    if not fullcmd:
        if not os.path.exists(command) or not os.access(command, os.X_OK):
            fullcmd = None

    if not fullcmd:
        print('Unable to locate command \'%s\' or you don\'t have the permission to execute the command' % command, file=sys.stderr)
        sys.exit(1)

    return fullcmd

def tar_gnu(tarcmd):
    proc = subprocess.Popen([tarcmd, '--version'], stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    
    if not re.search(r'tar \(GNU tar\)', stdout.strip(), re.MULTILINE):
        print('Error the tar command \'%s\' does not seem to be GNU tar' % tarcmd, file=sys.stderr)
        sys.exit(1)

def tar(cmn, source, destination):

    logger = cmn.get_logger(__name__ + '.tar')

    if cmn.cfg.getboolean('imager', 'compress'):
        taropts = [ cmn.cfg.get('commands', 'tar'), '-z', '-p', '-c', '-f', destination, '.']
    else:
        taropts = [ cmn.cfg.get('commands', 'tar'), '-p', '-c', '-f', destination, '.']

    logger.debug('running gnu tar command: %s' % ' '.join(taropts))
    proc = subprocess.Popen(taropts, cwd=source, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()

    return proc.returncode, stdout.strip().splitlines(), stderr.strip().splitlines()


def version_info(major, minor, micro, releaselevel='alpha', serial=0):
    level_hex = { 'alpha': 'a', 'beta':  'b','final': 'f', }

    if level_hex.has_key(releaselevel):
        rl = level_hex[releaselevel]
    else:
        rl = 'a'

    VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')
    vi          = VersionInfo(major=major, minor=minor, micro=micro, releaselevel=releaselevel, serial=serial)

    _hexstring = '0x%02d%02d%02d%s%d' % (
        major, minor, micro, rl, serial
    )
    return int(_hexstring, 16), vi

def parse_ip_command(data):

    ip4, ip6 = None, None
    for line in data.splitlines():
        if re.search(r'^inet\s.+', line.strip()):
            ip4 = line.strip().split()[1].split('/')[0]
        elif re.search(r'^inet6\s.+', line.strip()):
            ip6 = line.strip().split()[1].split('/')[0]
            ## Skip the link-local address
            if ip6.startswith('fe80'):
                ip6 = None
    return {'ipv4': ip4, 'ipv6': ip6}

def get_interfaces():
    for path in os.environ.get('PATH').split(os.pathsep):
        ippath = os.path.join(path, 'ip')
        if os.path.exists(ippath) and os.access(ippath, os.X_OK):
            ipcmd = ippath

    ## Step 1 fetch all interfaces and skip the lo
    interfaces = [ int for int in os.listdir('/sys/class/net') if not int in ['lo'] ]

    interfaces_data = dict()
    for interface in interfaces:
        proc = subprocess.Popen([ipcmd, 'addr', 'show', interface], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            continue

        interfaces_data[interface] = parse_ip_command(stdout)
    return interfaces_data


def run_command(*args, **kwargs):

    run_shell = kwargs.get('shell', False)
    if run_shell:
        args = " ".join(args)

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=run_shell)
    stdout, stderr = p.communicate()

    return p.returncode, stdout, stderr

def run_command_call(*args, **kwargs):

    run_shell = kwargs.get('shell', False)
    if run_shell:
        args = " ".join(args)

    return subprocess.call(args, shell=run_shell)

def img_is_locked(cmn, imagename):
    if os.path.exists(os.path.join(cmn.cfg.get('general', 'cache_dir'), 'processing/' + imagename)):
        return True
    return False

def img_lock(cmn, imagename, process):
    if img_is_locked(cmn, imagename):
        return True

    if not os.path.isdir(os.path.join(cmn.cfg.get('general', 'cache_dir'), 'processing')):
        os.mkdir(os.path.join(cmn.cfg.get('general', 'cache_dir'), 'processing'))

    with open(os.path.join(cmn.cfg.get('general', 'cache_dir'), 'processing/' + imagename), 'w') as fo:
        fo.write(process+'\n')

    return True

def img_unlock(cmn, imagename):
    if img_is_locked(cmn, imagename):
        os.remove(os.path.join(cmn.cfg.get('general', 'cache_dir'), 'processing/' + imagename))
        return True
    return False

def img_is_locked_by(cmn, imagename):
    if img_is_locked(cmn, imagename):
        with open(os.path.join(cmn.cfg.get('general', 'cache_dir'), 'processing/' + imagename), 'r') as fi:
            return fi.read().strip()
    return False

def _generate_index(string):
    '''Is used to generate a index, this way we can also sort nummeric values in a string'''
    return [ int(y) if y.isdigit() else y for y in re.split(r'(\d+)', string) ]
