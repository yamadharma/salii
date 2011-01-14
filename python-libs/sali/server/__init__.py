# "SALI"
#
# Copyright (c) 2010 SARA Computing and Networking Services
#
#   $Id: server.py 287 2010-11-30 15:11:19Z dennis $

## BitTornado uses the old sha module which is deprecated. So
## added a filter to ignore these DeprecationWarning.
import warnings
warnings.filterwarnings( 'ignore', category=DeprecationWarning )

## Import our module
from sali import process
from sali import general
from sali import monitor
from sali.server import tools

## Import some Python core modules
import sys
import time
import os
import subprocess
import socket
import signal

## Import some BitTornado modules
from BitTornado.BT1.track import track
from BitTornado.launchmanycore import LaunchMany
from BitTornado.download_bt1 import defaults, get_usage
from BitTornado.parseargs import parseargs
from BitTornado import version, report_email
from BitTornado.ConfigDir import ConfigDir

## Import PSYCO. note: Psyco only works on 32bit systems!
## Maybe I must remove this because we are only using 64bit
## systems.
from BitTornado import PSYCO

if PSYCO.psyco:
    try:
        import psyco
        assert psyco.__version__ >= 0x010100f0
        psyco.full()
    except:
        pass

## Some global variables
Exceptions = []
DEVELOPMENT = True

class Tracker( process.Task ):
    '''The Tracker Task, it wrappes the BitTornado bttrack command'''

    dstate = None

    def run( self ):

        self.log.info( 'started' )

        if '--dfile' in self.args:
            num = self.args.index( '--dfile' )

            self.dstate = self.args[ num + 1 ]

            if os.path.exists( self.args[ num + 1 ] ):
                self.log.debug( 'removing old dfile' )
                os.remove( self.args[ num + 1 ] )
        else:
            self.log.critical( 'variable dfile is required' )
            raise sali.StopTask()

        self.log.debug( 'starting tracker with args "%s"' % " ".join( self.args ) )
        track( self.args )

    def exit( self ):
        '''Cleanup any leftovers after running the tracker'''
        if self.dstate and os.path.exists( self.dstate ):
            self.log.debug( 'removing dstate file' )
            os.remove( self.dstate )
        process.Task.exit( self )

class SeederDisplayer:
    '''This class handles the display of the Seeder'''

    def display( self, data ):
        pass

    def message( self, s ):
        pass

    def exception( self, s ):
        Exceptions.append(s)

class Seeder( process.Task ):

    def run( self ):

        self.log.info( 'started' )

        defaults.extend( [
            ( 'parse_dir_interval', 60,
                "how often to rescan the torrent directory, in seconds" ),
            ( 'saveas_style', 1,
                "How to name torrent downloads (1 = rename to torrent name, " +
                "2 = save under name in torrent, 3 = save in directory under torrent name)" ),
            ( 'display_path', 1,
                "whether to display the full path or the torrent contents for each torrent" ),
        ] )

        try:
            configdir = ConfigDir( 'launchmany' )
            defaultsToIgnore = [ 'responsefile', 'url', 'priority' ]
            configdir.setDefaults( defaults, defaultsToIgnore )
            configdefaults = configdir.loadConfig()

            config, args = parseargs( self.args, defaults, 1, 1, configdefaults )
            configdir.deleteOldCacheData( config[ 'expire_cache_data' ] )
            config[ 'torrent_dir' ] = args[ 0 ]
        except ValueError, e:
            print( 'Error: %s some error' % str( e ) )
            sys.exit( 1 )

        self.log.debug( 'start seeder with args "%s"' % " ".join( self.args ) )
        LaunchMany( config, SeederDisplayer() )

class SaliMonitor( process.Task ):

    def __init__( self, logging, cfg ):
        process.Task.__init__( self, logging )

        if not cfg.has_option( 'DEFAULT', 'serveraddress' ) or not cfg.has_option( 'monitor', 'port' ):
            self.log.critical( 'Need serveraddres and port' )
            sys.exit( 1 )

        try:
            self.server = monitor.SaliMonitorServer(
                ( 
                    cfg.get_default( 'serveraddress' ) , 
                    cfg.getint( 'monitor', 'port' )   
                ), 
                monitor.SaliMonitorHandler,
                cfg,
                logging 
            )
        except ValueError:
            self.log.critical( 'Port must be a integer' )
            sys.exit( 1 )
        except socket.error, err:
            self.log.critical( 'Socket error: %s' % err )
            sys.exit( 1 )

    def run( self ):
        self.log.info( 'started' )
        self.server.serve_forever()

class UpdateImages( process.Task ):

    def __init__( self, logging, cfg ):
        process.Task.__init__( self, logging )
        self.images = list()

        ## Gather the images that we must monitor
        if cfg.has_option( 'update', 'images' ):
            self.images = cfg.get( 'update', 'images' ).replace( ' ', '' ).split( ',' )

        ## Check the sleeptime, if in DEVELOPMENT all values are accepted
        if cfg.has_option( 'update', 'sleeptime' ):
            try:
                self.sleeptime = cfg.getint( 'update', 'sleeptime' )
            except ValueError:
                self.log.critical( 'value of sleeptime must be a integer' )
                sys.exit( 1 )
        else:
            self.sleeptime = 300

        global DEVELOPMENT
        if not self.sleeptime >= 300 and not DEVELOPMENT:
            self.log.critical( 'minimal wait time is 5 minutes!' )
            sys.exit( 1 )

        self.ci = tools.CreateImage( logging, cfg )
        self.log.info( 'started' )
        self.cfg = cfg

    def check_imagedir( self ):
   
        ifiles = list()
 
        for file in os.listdir( self.ci.imagedir ):
            if file in self.images:
                ifiles.append( file )

        return ifiles

    def human_time( self, seconds ):
        rest_sec = seconds % 60
        minutes = ( seconds - rest_sec ) / 60

        if minutes > 1:
            mplural = 's'
        else:
            mplural = ''

        if rest_sec > 1:
            splural = 's'
        else:
            splural = ''

        if int( rest_sec ) > 0:
            return "%s minute%s and %s second%s" % ( minutes, mplural, rest_sec, splural )
        else:
            return "%s minute%s" % ( minutes, mplural )

    def run( self ):

        while True:
            self.log.info( 'starting check' )
            images = self.check_imagedir()

            if images:
                for image in images:
                   
                    no_tarball = os.path.join( self.cfg.get_default( 'maindir' ), 'notorrent' )
                    if os.path.exists( os.path.join( no_tarball, image ) ):
                        self.log.info( '%s%s: getimage in progress, skipping tarball creation' % ( self.ci.space( 2 ), image ) )
                        self.log.info( 'sleeping for %s' % self.human_time( self.sleeptime ) )
                        time.sleep( self.sleeptime )
                    else:
                        if self.ci.is_tar( self.ci.tarball_location( image ) ):
                            try:
                                if os.path.getmtime( os.path.join( self.ci.imagedir, image ) ) > os.path.getmtime( self.ci.tarball_location( image ) ):
                                    self.log.info( '%s%s: tarball of image is out of date, creating a new one' % ( self.ci.space( 2 ), image ) )
                                    os.remove( self.ci.tarball_location( image ) )
                                    self.ci.check_metafiles( image, self.ci.tarball_location( image ), remove=True )
                                    self.ci.create_tarball( image )
                                else:
                                    self.log.info( '%s%s: tarball of image is up to date' % ( self.ci.space( 2 ), image ) )
                                    self.ci.check_metafiles( image, self.ci.tarball_location( image ) )
                            except OSError, err:
                                self.log.critical( '%s: %s error %s' % ( image, self.ci.space( 2 ), str( err ) ) )
                                sys.exit( 1 )
                        else:
                            self.ci.create_tarball( image )
            self.log.info( 'sleeping for %s' % self.human_time( self.sleeptime ) )
            time.sleep( self.sleeptime )

class sali_server( general.Daemon ):

    def __init__( self, cfg, logging, pidfile, workpath='/' ):
        general.Daemon.__init__( self, cfg, logging, pidfile, workpath )
        signal.signal( signal.SIGTERM, self.handler )

        self.log = self.logging.getLogger( 'SaliServer' )

    def handler( self, signal, frame ):
        if os.path.exists( self.pidfile ):
            print( 'Removing pidfile, caugth a signal' )
            os.remove( self.pidfile )
        sys.exit()

    def run( self ):
        self.log.info( 'starting threads' )

        if self.cfg.do_tracker() or self.cfg.do_bittorrent():
            if not self.cfg.has_option( 'bittorrent', 'torrentsdir' ):
                print( 'Could not find variable torrentsdir in section bittorrent ( required )' )
                sys.exit( 1 )

        self.process = process.Process()

        if self.cfg.do_tracker():
            ## Parsing the configuration to arguments.
            targs = self.cfg.get_params( 'tracker', append='--' )

            ## If not set set now
            if not '--allowed_dir' in targs:
                targs.append( '--allowed_dir' )
                targs.append( self.cfg.get( 'bittorrent', 'torrentsdir' ) )

            self.process.append( Tracker( self.logging, args=targs ) )

        if self.cfg.do_bittorrent():
            ## Parsing the options for the seeder
            sargs = self.cfg.get_params( 'seeder', append='--' )
            sargs.insert( 0, self.cfg.get( 'bittorrent', 'torrentsdir' ) )

            self.process.append( Seeder( self.logging, args=sargs ) )

        if self.cfg.do_updateimages():
            self.process.append( UpdateImages( self.logging, cfg=self.cfg ) )

        if self.cfg.do_monitor():
            self.process.append( SaliMonitor( self.logging, cfg=self.cfg ) )

        try:
            self.process.run()
        except KeyboardInterrupt:
            print( 'Recieved keyboardinterrupt stopping sali_server' )

