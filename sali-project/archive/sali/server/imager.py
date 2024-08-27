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
import time
import tarfile

from sali import tools
from sali.torrent import CreateTorrent

def imager_run(cmn):
    imager = Imager(cmn)

    while True:
        try:
            if not imager.run():
                break
            imager.logger.debug('sleeping for %s seconds' % cmn.cfg.getint('imager', 'sleep'))
            time.sleep(cmn.cfg.getint('imager', 'sleep'))
        except KeyboardInterrupt:
            break

class Imager(object):

    def __init__(self, cmn):
        self.cmn = cmn
        self.logger = cmn.get_logger(__name__ + '.Imager')

        self.logger.debug('initializing imager')

    def run(self):
        if not self.cmn.cfg.has_option('imager', 'images'):
            self.logger.warning('imager has been enabled but no images defined in imager.images, please update your configuration and restart sali')
            return False

        ## loop trough the images
        for image in self.cmn.cfg.get('imager', 'images').split(','):
            image = image.strip()

            if tools.img_is_locked(self.cmn, image):
                self.logger.debug('image %s is locked by a getimage process' % image)
                return True

            tools.img_lock(self.cmn, image, 'server::imager')

            self.logger.debug('checking condition of image %s' % image)

            if os.path.exists(os.path.join(self.cmn.cfg.get('general', 'data_dir'), 'images') + '/' + image):
                self.create_tarfile(image)
                self.create_torrentfile(image)
            else:
                self.logger.debug('image %s does not exist' % image)

            tools.img_unlock(self.cmn, image)

        return True

    def up2date(self, tarpath, imagepath):
        if os.path.getmtime(imagepath) > os.path.getmtime(tarpath):
            return False
        return True

    def create_tarfile(self, image):
   
        create_image    = False
        imagepath       = os.path.join(self.cmn.cfg.get('general', 'data_dir'), 'images') + '/' + image
        if self.cmn.cfg.getboolean('imager', 'compress'):
            tarpath     = os.path.join(self.cmn.cfg.get('general', 'data_dir'), 'torrents') + '/image-%s.tar.gz' % image
        else:
            tarpath     = os.path.join(self.cmn.cfg.get('general', 'data_dir'), 'torrents') + '/image-%s.tar' % image

        if not os.path.exists(tarpath):
            self.logger.debug('tarball %s does not exists for image %s' % (tarpath, image))
            create_image = True

        if not create_image and not self.up2date(tarpath, imagepath):
            self.logger.debug('image has been updated in %s creating a new tarfile' % imagepath)
            create_image = True

        if create_image:
            self.logger.debug('creating new tarfile for image %s' % image)
            rcode, stdout, stderr = tools.tar(self.cmn, imagepath, tarpath)

            if rcode != 0:
                self.logger.critical('an error has occured during tarfile creation: %s' % str(stderr))
            else:
                self.logger.debug('finished creating tarball for image %s' % image)
        else:
            self.logger.debug('image for %s seems ok' % image)
        
    def create_torrentfile(self, image):
        if self.cmn.cfg.getboolean('imager', 'compress'):
            tarpath     = os.path.join(self.cmn.cfg.get('general', 'data_dir'), 'torrents') + '/image-%s.tar.gz' % image
        else:
            tarpath     = os.path.join(self.cmn.cfg.get('general', 'data_dir'), 'torrents') + '/image-%s.tar' % image
        create_torrent  = False

        if not os.path.exists(tarpath+'.torrent'):
            self.logger.debug('torrent file for image %s does not exists' % image)
            create_torrent = True

        if not create_torrent and not self.up2date(tarpath+'.torrent', tarpath):
            self.logger.debug('torrent file is out of date for image %s' % image)
            create_torrent = True

        if create_torrent:
            self.logger.debug('creating new torrent file for image %s' % image)
            torrent = CreateTorrent(self.cmn, tarpath)
            torrent.write_torrent()
            self.logger.debug('done creating torrent file for image %s' % image)
