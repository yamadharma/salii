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
import platform
from datetime import timedelta

from tornado import web

from sali.tools import get_uptime

class AboutHandler(web.RequestHandler):

    def get(self, args):


        about_data = {
            'os_type': os.uname()[0],
            'os_release': os.uname()[2],
            'os_uptime': get_uptime(),
            'os_distro': ' '.join(platform.dist()),

            'sali_version': '2.0.0',
        }

        self.render('about.html', **about_data)
