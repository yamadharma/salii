#
# This file is part of SALII
#
# SALII is free software: you can redistribute it and/or modify
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
# Copyright 2010-2024 Dmitry S. Kulyabov

from sali.tools import version_info

name            = 'salii'
## See also https://packaging.python.org/en/latest/distributing.html#version
hexversion, version_info  = version_info(1,7,0,'',0)
if version_info.releaselevel:
    version         = '%d.%d.%d%s' % (version_info.major, version_info.minor, version_info.micro, version_info.releaselevel)
else:
    version         = '%d.%d.%d' % (version_info.major, version_info.minor, version_info.micro)
copyright       = 'Copyright (c) 2010-2024 Dmitry S. Kulyabov'
description     = 'SALII is used to image and install Linux machine with rsync or bittorrent.'
author          = 'Dmitry S. Kulyabov'
author_email    = 'yamadharma@gmail.com'
url             = 'https://github.com/yamadharma/salii'
license         = 'GPL'
download_url    = '%s' % (version)
keywords        = ['SURF', 'SystemImager', 'SALII', 'installer', 'tornando', 'bittorrent', 'linux']
