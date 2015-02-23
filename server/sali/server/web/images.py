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
import json
from datetime import datetime

from sali import release
from sali import tools
from sali.server.web import base

class Images(object):
    
    def __init__(self, cmn):
        self.cmn = cmn

    def find_images(self):

        torrent_images = [ image.strip() for image in self.cmn.cfg.get('imager', 'images').split(',') ]

        outlist = list()
        path = os.path.join(self.cmn.cfg.get('general', 'data_dir'), 'images')
        for image in os.listdir(path):
            is_locked_by = tools.img_is_locked_by(self.cmn, image)
            outlist.append({
                'imagename': image,
                'mtime': datetime.fromtimestamp(os.path.getmtime(os.path.join(path, image))).isoformat('T'),
                'tarball': 'yes' if image in torrent_images else 'no',
                'is_locked': True if is_locked_by is not False else False,
                'is_locked_by': is_locked_by
            })
        return outlist

class ImagesHandler(base.SaliRequestHandler):

    def get(self, args):
        imgs = Images(self.cmn)
        images_data = imgs.find_images()

        self.render('images.html', **{'sali_version': release.version, 'images': images_data})
