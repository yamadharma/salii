#!/usr/bin/env python
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

####
##  PLEASE EDIT sali.release WHEN RELEASING A NEW VERSION, DOT NOT EDIT METAINFO
##  IN THIS FILE!!
####


## Include the disturils core
from distutils.core import setup

## Include the SALI release module for version info, description, etc
from sali import release

if release.version_info.releaselevel == 'alpha':
    dev_status = '3 - Aplha'
elif release.version_info.releaselevel == 'beta':
    dev_status = '4 - Beta'
else:
    dev_status = '5 - Production/Stable'

setup(
    ## Meta information
    name=release.name,
    version=release.version,
    author=release.author,
    author_email=release.author_email,
    url=release.url,
    description=release.description,
    long_description=open('README').read()
    license=release.license,
    keywords=release.keywords,
    download_url=release.download_url,

    ## PyPi specific stuff
    classifiers = [
        'Development Status :: ' + dev_status,
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    install_requires = [
        'tornado>=4.0'
    ],

    ## Specific packaging stuff
    packages=['sali'],
    scripts=['bin/sali'],
    data_files = [
        ('/etc/sali', [
            'files/sali.cfg',
        ]),
        ('/etc/sali/rsync_stubs', [
            'files/rsync_stubs/00header.conf',
        ]),
        ('/etc/sali/exclude_files', [
            'files/exclude_files/default.excl',
            'files/exclude_files/global.excl',
        ]),
    ],
)
