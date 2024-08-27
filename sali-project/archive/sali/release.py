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
ROOT_DIR=os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))

from sali.tools import version_info

name            = 'sali-server'
## See also https://packaging.python.org/en/latest/distributing.html#version
hexversion, version_info  = version_info(1,7,0,'.dev1',0)
if version_info.releaselevel:
    version         = '%d.%d.%d%s' % (version_info.major, version_info.minor, version_info.micro, version_info.releaselevel)
else:
    version         = '%d.%d.%d' % (version_info.major, version_info.minor, version_info.micro)
copyright       = 'Copyright (c) 2008-2014 SURFsara'
description     = 'SALI is used to image and install Linux machine with rsync or bittorrent, see https://oss.trac.surfsara.nl/sali for more information.'
author          = 'SURFsara'
author_email    = 'sali@surfsara.nl'
url             = 'https://oss.trac.surfsara.nl/sali'
license         = 'GPL'
download_url    = 'https://pypi.python.org/packages/source/s/sali-server/sali-server-%s.tar.gz' % (version)
keywords        = ['SURFsara', 'SystemImager', 'SALI', 'installer', 'tornando', 'bittorrent', 'linux']
