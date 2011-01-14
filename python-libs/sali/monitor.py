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
from xml.etree import ElementTree
from xml.etree.ElementTree import SubElement

class SaliMonitorServer( TCPServer ):

    def __init__( self, server_address, handler, cfg, logging ):
        TCPServer.__init__( self, server_address, handler )
        self.log  = logging.getLogger( self.__class__.__name__ )
        self.cfg = cfg

class SaliMonitorHandler( BaseRequestHandler ):

    BASEDATA    = [ 'time', 'mac', 'ip', 'host', 'cpu', 'ncpus', 'kernel', 'mem', 'tmpfs', 'status', 'speed', 'tmpfs', 'os' ]
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

    def si_save_data( self, data ):
        '''A method for saving the data so the gui tool si_monitortk can be used'''

        if not self.server.cfg.has_option( 'monitor', 'si_monitortk' ) and not self.server.cfg.getboolean( 'monitor', 'si_monitortk' ):
            return

        ## In the xml mac == name
        name = data[ 'mac' ].lower()
        del data[ 'mac' ]

        try:
            fi = open( self.server.cfg.get( 'monitor', 'si_clients' ), 'rt' )
            tree = ElementTree.parse( fi )
            updated = False

            for child in tree.findall( './/client' ):
                if child.get( 'name' ).lower() == name.lower():
                    child.attrib[ 'name' ] = name
                    for key,value in data.items():
                        child.attrib[ key ] = str( value )
                        updated = True

            if not updated:
                father = tree.getroot()

                attribs = dict()          
                attribs[ 'name' ] = name 

                for key, value in data.items(): 
                    attribs[ key ] = str( value )

                append = SubElement( father, 'client', attribs )

            tree.write( self.server.cfg.get( 'monitor', 'si_clients' ) )
            fi.close()
        except Exception:
            tree = ElementTree.Element('opt')

            child = ElementTree.SubElement( tree, 'client' )

            child.attrib[ 'name' ] = str( name )
            for key,value in data.items():
                child.attrib[ key ]  = str( value )

            fo = open( self.server.cfg.get( 'monitor', 'si_clients' ), 'w' )
            fo.write( ElementTree.tostring( tree ) )
            fo.close()

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
                pdata[ mac ][ key ] = value

            pickle.dump( pdata, open( self.cfgfile, 'w' ) )
            self.si_save_data( pdata[ mac ] )

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
            self.server.log.info( 'could not save the data of client "%s", %s' % ( self.client_address[ 0 ], data ) )
