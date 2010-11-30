# "SALI"
#
# Copyright (c) 2010 SARA Computing and Networking Services
#
#   $Id$

# Python modules
import time
import types
import os
import cPickle as pickle
from SocketServer import TCPServer
from SocketServer import BaseRequestHandler

class SaliMonitorServer( TCPServer ):

    def __init__( self, server_address, handler, cfg, logging ):
        TCPServer.__init__( self, server_address, handler )
        self.log  = logging.getLogger( self.__class__.__name__ )
        self.cfg = cfg

class SaliMonitorHandler( BaseRequestHandler ):

    BASEDATA    = [ 'mac', 'ip', 'host', 'cpu', 'ncpus', 'kernel', 'mem', 'tmpfs', 'status', 'speed', 'tmpfs', 'os' ]
    cfgfile     = '/var/tmp/sali/monitor.data'

    def parse_data( self, data ):

        rdict = dict()

        for item in data.split( ':' ):
            items = item.split( '=' )

            if len( items ) != 2:
                self.server.log.warning( 'invalid data, skipped' )
                continue

            if items[ 0 ] in self.BASEDATA:
                rdict[ items[ 0 ] ] = items[ 1 ]

        return rdict

    def save_data( self, data ):

        if data.has_key( 'mac' ):
            if os.path.exists( self.cfgfile ):
                pdata = pickle.load( open( self.cfgfile, 'r' ) )
            else:
                pdata = dict()

            mac = data[ 'mac' ]

            if not pdata.has_key( mac ) or not type( pdata[ mac ] ) is types.DictType:
                pdata[ mac ] = dict()

            timestamp = int( time.time() )

            #Checking first_timestamp
            if not pdata[ mac ].has_key( 'first_timestamp' ):
                pdata[ mac ][ 'first_timestamp' ] = timestamp

            #Updating timestamp
            pdata[ mac ][ 'timestamp' ] = timestamp

            for key, value in data.items():
                pdata[ key ] = value

            pickle.dump( pdata, open( self.cfgfile, 'w' ) )

            return True

        return False

    def handle( self ):
        # self.request is the TCP socket connected to the client
        data = self.request.recv( 1024 ).strip()
        self.server.log.debug( 'data recieved from "%s"' % self.client_address[ 0 ] )
        ddict = self.parse_data( data )

        if self.save_data( ddict ):
            self.server.log.debug( 'the data of client "%s" has been saved' % self.client_address[ 0 ] )
        else:
            self.server.log( 'could not save the data of client "%s", %s' % ( self.client_address[ 0 ], data ) )
