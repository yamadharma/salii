
# Must be imported first
from __future__ import print_function

## Import our module
from sali import process
from sali import general
from sali import monitor

## Import some Python core modules
import sys
import shutil
import time
import os
import subprocess
import operator

## Import some BitTornado modules
from BitTornado.BT1.track import track
from BitTornado.launchmanycore import LaunchMany
from BitTornado.download_bt1 import defaults, get_usage
from BitTornado.parseargs import parseargs
from BitTornado import version, report_email
from BitTornado.ConfigDir import ConfigDir
from BitTornado.BT1.makemetafile import make_meta_file

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

class UpdateImages( process.Task ):
    '''Checks if the tarball/metafile is up to date'''

    def __init__( self, logging, cfg ):
        self.images = list()
        self.taropts = [ '-p', '-c', '-f' ]
        self.tarballext = 'tar'
        self.meta_exts = {
            'torrent': self.create_torrent,
        }

        process.Task.__init__( self, logging )

        if not cfg.has_option( 'update', 'imagedir' ) or not os.path.exists( cfg.get( 'update', 'imagedir' ) ):
            self.log.critical( 'could not locate imagedir, check your configuration' )
            sys.exit( 1 )
        else:
            self.imagedir = cfg.get( 'update', 'imagedir' )

        if not cfg.has_option( 'bittorrent', 'torrentsdir' ) or not os.path.exists( cfg.get( 'bittorrent', 'torrentsdir' ) ):
            self.log.critical( 'could not locate torrentsdir, check your configuration' )
            sys.exit( 1 )
        else:
            self.torrentsdir = cfg.get( 'bittorrent', 'torrentsdir' )

        if not cfg.has_option( 'update', 'trackeradress' ):
            self.log.critical( 'trackeradress must be configured' )
            sys.exit( 1 )
        else:
            self.trackeradress = cfg.get( 'update', 'trackeradress' )

        if cfg.has_option( 'update', 'images' ):
            self.images = cfg.get( 'update', 'images' ).replace( ' ', '' ).split( ',' )

        if cfg.has_option( 'update', 'sleeptime' ):
            try:
                self.sleeptime = cfg.getint( 'update', 'sleeptime' )
            except ValueError:
                self.log.critical( 'value of sleeptime must be a integer' )
                sys.exit( 1 )
        else:
            self.sleeptime = 300

        if not cfg.has_option( 'update', 'tarcommand' ) or not os.path.exists( cfg.get( 'update', 'tarcommand' ) ):
            self.taropts.insert( 0, self.find_tar() )
        elif not os.path.exists( cfg.get( 'update', 'tarcommand' ) ):
            self.log.critical( 'could not locate tarcommand, check your config' )
            sys.exit( 1 )

        global DEVELOPMENT
        if not self.sleeptime >= 300 and not DEVELOPMENT:
            self.log.critical( 'minimal wait time is 5 minutes!' )
            sys.exit( 1 )

        if cfg.has_option( 'update', 'compress' ):
            try:
                if cfg.getboolean( 'update', 'compress' ):
                    self.tarballext = 'tar.gz'
                    self.taropts.insert( 1, '-z' )
            except ValueError:
                pass

    def space( self, level=0 ):
        return " " * level

    def find_tar( self ):
        p = subprocess.Popen( 
            [ 'which', 'tar' ], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE 
        )

        sti, ste = p.communicate()

        if not p.returncode == 0:
            self.log.critical( 'an error has occured, so cannot find tar command' )
            sys.exit( 1 )

        if not os.path.exists( sti.strip() ):
            self.log.critical( 'could not locate tar command' )
            sys.exit( 1 )

        return sti.strip()

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

    def is_tar( self, filename ):
       
        if os.path.exists( filename ): 
            p = subprocess.Popen( 
                [ 'file', '-b', '--mime-type', filename ], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE 
            )

            sti, ste = p.communicate()

            if not p.returncode == 0:
                return False

            if sti.strip() in [ 'application/x-tar', 'application/x-gzip' ]:
                return True

        return False

    def check_imagedir( self ):
   
        ifiles = list()
 
        for file in os.listdir( self.imagedir ):
            if file in self.images:
                ifiles.append( file )

        return ifiles

    def display_torrent( self, complete ):
        percent = operator.mul( complete, 100 )

        if percent >= 100:
            self.log.info( '%s torrent file has been created' % self.space( 6 ) )

    def create_torrent( self, targetfile ):

        params = dict( target='%s.torrent' % targetfile )

        make_meta_file( targetfile, self.trackeradress, progress=self.display_torrent, params=params ) 

    def create_metafiles( self, imagename, targetfile ):

        for mtype, mfunc in self.meta_exts.items():
            self.log.info( '%s%s: creating %s file' % ( self.space( 4 ), imagename, mtype ) )
            mfunc( targetfile )

    def create_tarball( self, imagename ):

        self.log.info( '%s%s: creating tarball %s from %s' % 
            ( 
                self.space( 4 ),
                imagename, 
                self.tarball_location( imagename ),
                os.path.join( self.imagedir, imagename )
            )
        )

        opts = list()
        opts.extend( self.taropts )
        opts.append( '%s.tmp' % self.tarball_location( imagename ) )
        opts.append( '.' )

        self.log.debug( '%s%s: %s' % ( self.space( 4 ), imagename, " ".join( opts ) ) )

        p = subprocess.Popen( 
            opts, 
            cwd=os.path.join( self.imagedir, imagename ), 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        sti, ste = p.communicate()

        if p > 0:
            if ste.strip():
                for line in ste.split( '\n' ):
                    if line.strip():
                        self.log.warning( line.strip() )

        self.log.debug( '%s%s: moving %s.tmp to %s' % ( self.space( 4 ), imagename, self.tarball_location( imagename ), self.tarball_location( imagename ) ) )
        shutil.move( '%s.tmp' % self.tarball_location( imagename ), self.tarball_location( imagename ) )
        self.log.debug( '%s%s: tarball has been created' % ( self.space( 4 ), self.tarball_location( imagename ) ) )

        self.create_metafiles( imagename, self.tarball_location( imagename ) )

    def tarball_location( self, image ):
        return os.path.join( 
            self.torrentsdir, 'image-%s.%s' % ( image, self.tarballext ) 
        )

    def check_metafiles( self, image, targetfile, remove=False ):
        for metafile in self.meta_exts.keys():
            if os.path.exists( '%s.%s' % ( targetfile, metafile ) ):
                if not remove:
                    if os.path.getmtime( targetfile ) > os.path.getmtime( '%s.%s' % ( targetfile, metafile ) ):
                        self.log.info( '%s%s: metafile %s is out of date, creating a new one' % ( self.space( 4 ), image, metafile ) )
                        os.remove( '%s.%s' % ( targetfile, metafile ) )
                        self.create_metafiles( image, targetfile )
                else:
                    os.remove( '%s.%s' % ( targetfile, metafile ) )
            else:
                self.log.info( '%s%s: does not have a %s metafile, creating it now' % ( self.space( 4 ), image, metafile ) )
                self.create_metafiles( image, targetfile )
                                        
    def run( self ):

        while True:
            self.log.info( 'starting check' )
            images = self.check_imagedir()

            if images:
                for image in images:
                    if self.is_tar( self.tarball_location( image ) ):
                        try:
                            if os.path.getmtime( os.path.join( self.imagedir, image ) ) > os.path.getmtime( self.tarball_location( image ) ):
                                self.log.info( '%s%s: tarball of image is out of date, creating a new one' % ( self.space( 2 ), image ) )
                                os.remove( self.tarball_location( image ) )
                                self.check_metafiles( image, self.tarball_location( image ), remove=True )
                                self.create_tarball( image )
                            else:
                                self.log.info( '%s%s: tarball of image is up to date' % ( self.space( 2 ), image ) )
                                self.check_metafiles( image, self.tarball_location( image ) )

                        except OSError, err:
                            self.log.critical( '%s: %s error %s' % ( image, self.space( 2 ), str( err ) ) )
                            sys.exit( 1 )
                    else:
                        self.create_tarball( image )
            self.log.info( 'sleeping for %s' % self.human_time( self.sleeptime ) )
            time.sleep( self.sleeptime )

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

    def run( self ):
        self.server.serve_forever()

class sali_server( general.Daemon ):

    def __init__( self, cfg, fg=False ):

        if not fg:
            self.daemon = True

        if not cfg.has_option( 'DEFAULT', 'pidfile' ):
            print( 'You must have a pidfile variable in DEFAULT section' )
            sys.exit( 1 )

        if not cfg.has_option( 'DEFAULT', 'logfile' ):
            print( 'Variable logifile must be set in section DEFAULT' )
            sys.exit( 1 )

        if not cfg.has_option( 'DEFAULT', 'loglevel' ):
            print( 'Variable loglevel must be set in section DEFAULT' )
            sys.exit( 1 )

        try:
            self.logging =  general.Logging( 
                                cfg.get_default( 'logfile' ),
                                cfg.getint( 'DEFAULT', 'loglevel' )
                            )
            self.logging.daemon = self.daemon
        except ValueError:
            print( 'Value of loglevel must be a integer' )
            sys.exit( 1 )

        self.cfg = cfg
        self.log = self.logging.getLogger( 'SaliServer' )

        if fg:
            self.log.info( 'starting in forground' )
        else:
            self.log.info( 'starting as daemon' )

        general.Daemon.__init__( self, cfg.get_default( 'pidfile' ) )

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

