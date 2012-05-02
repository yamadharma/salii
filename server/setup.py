#!/usr/bin/env python
#
# Copyright (C) 2008-2010 SARA Computing and Networking Services
#
# set ts=4, sw=4
#

from distutils.core import setup

setup(
        name = 'SALI',
        version = '1.5.0',

        description = 'sali server and utilities',
        long_description = 'sali server and utilities',
        author = 'Dennis Stam',
        author_email = 'sali@sara.nl',
        url = 'https://subtrac.sara.nl/oss/sali',
        license = 'GPL',
        
        classifiers = [
                'Development Status :: 1 Planning',
                'Environment :: Console',
                'Intended Audience :: System Administrators',
                'License :: OSI Approved :: GNU General Public License (GPL)',
                'Natural Language :: English',
                'Operating System :: Unix',
                'Programming Language :: Python',
                'Topic :: System :: System Administration',
        ],

        packages = ['sali','sali.server','SaliBitTornado','SaliBitTornado.BT1'],
        scripts = ['scripts/sali','scripts/sali_server'],
        data_files = [ 
        (   '/etc/sali', [ 
                'config/sali.cfg', 
                'config/getimage.exclude',
            ] ),
        (   '/etc/sali/rsync_stubs', [
                'config/rsync_stubs/00header.conf',
            ] )
        ],
)
