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

import logging
import httplib

from tornado import web
from tornado import ioloop
from tornado import httpserver
from tornado import template
import tornado.gen

from sali.server.web import dashboard
from sali.server.web import images
from sali.server.web import about
from sali.server.web import tracker
from sali import common
from sali import database

def web_app(cmn):
    if not isinstance(cmn, common.Common):
        raise Exception('Variable cmn must be an instance of sali.common.Common')

    logger = cmn.get_logger(__name__ + '.web_app')

    logger.debug('intializing web interface')
    loader = template.Loader(cmn.cfg.get('web', 'templates'))

    # Pytt response messages
    RESPONSE_MESSAGES = {
        tracker.INVALID_REQUEST_TYPE: 'Invalid Request type',
        tracker.MISSING_INFO_HASH: 'Missing info_hash field',
        tracker.MISSING_PEER_ID: 'Missing peer_id field',
        tracker.MISSING_PORT: 'Missing port field',
        tracker.INVALID_INFO_HASH: 'info_hash is not %s bytes' % cmn.cfg.get('web', 'info_hash_len'),
        tracker.INVALID_PEER_ID: 'peer_id is not %s bytes' % cmn.cfg.get('web', 'peer_id_len'),
        tracker.INVALID_NUMWANT: 'Peers more than %s is not allowed.' % cmn.cfg.get('web', 'max_allowed_peers'),
        tracker.GENERIC_ERROR: 'Error in request',
    }
    httplib.responses.update(RESPONSE_MESSAGES)

    tracker_db = database.Database(cmn, 'tracker')
    monitor_db = database.Database(cmn, 'monitor')

    application = web.Application([
        (r'/', web.RedirectHandler, {'url': '/dashboard'}),
        (r'/dashboard(.*)', dashboard.DashBoardHandler ),
        (r'/images(.*)', images.ImagesHandler, dict(cmn=cmn) ),
        (r'/about(.*)', about.AboutHandler ),
        (r'/torrent-stats(.*)', tracker.StatsHandler, dict(cmn=cmn, db=tracker_db)),
        (r'/announce.*', tracker.AnnounceHandler, dict(cmn=cmn, db=tracker_db)),
    ],**{
        'template_path': cmn.cfg.get('web', 'templates'),
        'static_path': cmn.cfg.get('web', 'http_static'),
    })

    logger.debug('starting web interface')

    ## Owke, get the loggers and set propagate to False so the
    ## tornado module will not add any handlers!
    #cmn.get_logger('tornado.access').propagate = False
    #cmn.get_logger('tornado.application').propagate = False
    #cmn.get_logger('tornado.general').propagate = False

    http_server = httpserver.HTTPServer(application)
    http_server.listen(cmn.cfg.getint('web', 'port'), cmn.cfg.get('web', 'listen'))
    main_loop = ioloop.IOLoop.instance()
    main_loop.start()
