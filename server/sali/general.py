# "SALI"
#
# Copyright (c) 2010 SARA Computing and Networking Services
#
#   $Id$

## Python modules
import os
import signal
import sys
import atexit
import logging
import time
from logging import handlers
from ConfigParser import SafeConfigParser
from ConfigParser import NoSectionError
from ConfigParser import NoOptionError
from ConfigParser import InterpolationDepthError
from ConfigParser import InterpolationMissingOptionError

class Config( SafeConfigParser ):

    def __init__( self, cfgfile ):
        SafeConfigParser.__init__( self )
        self.readfp( open( cfgfile ) )

        if not self.has_section( 'bittorrent' ):
            print 'Missing the bittorrent configuration in the given file, check the documentation!'
            sys.exit( 1 )

    def options_default( self, section ):
        try:
            opts = self._sections[ section ].copy()
        except KeyError:
            raise NoSectionError( section )

    def options( self, section ):
        """Return a list of option names for the given section name.
        Without the options in the default section"""
        try:
            opts = self._sections[section].copy()
        except KeyError:
            raise errors.OptionparserException( 'No section %s found' % section)
        
        if '__name__' in opts:
            del opts[ '__name__' ]

        return opts.keys()

    def options_dict( self, section ):
        opts = dict()
        
        for key in self.options( section ):
            opts[ key ] = self.get( section, key )

        return opts

    def get_default( self, option ):
        if self.has_option( 'DEFAULT', option ):
            try:
                value = self.get( 'DEFAULT', option )
            except InterpolationMissingOptionError, detail:
                print 'could not get value for option: %s\n %s' %(option, detail)
                sys.exit(1)
            return value

    def do_bittorrent( self ):
        try:
            if self.getboolean( 'bittorrent', 'enable_bittorrent' ):
                return True
        except NoOptionError:
            return False

        return False

    def do_tracker( self ):
        try:
            if self.getboolean( 'bittorrent', 'enable_tracker' ):
                return True
        except NoOptionError:
            return False

        return False

    def do_updateimages( self ):
        try:
            if self.getboolean( 'update', 'enabled' ):
                return True
        except NoOptionError:
            return False

        return False

    def do_monitor( self ):
        try:
            if self.getboolean( 'monitor', 'enabled' ):
                return True
        except NoOptionError:
            return False

        return False

    def get_params( self, section, append='' ):

        args = list()

        for opt in self.options_dict( section ):
            args.append( '%s%s' % ( append, opt ) )
            args.append( self.get( section, opt ) )

        return args

class Logging( object ):

    LEVELS = {
        0 : logging.NOTSET,
        1 : logging.DEBUG,
        2 : logging.INFO,
        3 : logging.WARNING,
        4 : logging.ERROR,
        5 : logging.CRITICAL,
    }
    daemon = False
    
    def __init__( self, logfile, level ):
        self.logfile = logfile

        if level not in self.LEVELS.keys():
            print 'Configured level is incorrect choose 0 - 5'

        self.level = self.LEVELS[ level ]

    def getLogger( self, name, cli=False ):

        logger = logging.getLogger( name )
        logger.setLevel( logging.DEBUG )
    
        if not self.daemon or cli:
            ch = logging.StreamHandler()

            if self.level == logging.DEBUG:
                ch.setLevel( logging.DEBUG )
            else:
                ch.setLevel( logging.INFO )

            if cli:
                ch.setFormatter( logging.Formatter( '%(message)s' ) )
            else:
                ch.setFormatter( logging.Formatter( '%(name)-12s: %(levelname)-7s -- %(message)s' ) )
            logger.addHandler( ch ) 

        if not cli:
            #fh = logging.FileHandler( self.logfile )
            fh = handlers.TimedRotatingFileHandler( self.logfile, when='D', interval=1, backupCount=14 )
            fh.setLevel( self.level )
            fh.setFormatter( logging.Formatter( '%(asctime)s - %(name)-12s - %(levelname)-7s - %(message)s' ) )
            logger.addHandler( fh )

        return logger

class Daemon:

    def __init__( self, cfg, logging, pidfile, workpath='/' ):
        self.pidfile = pidfile
        self.workpath = workpath
        self.cfg = cfg
        self.logging = logging

    def perror( self, msg, err ):
        sys.stderr.write( msg.format( err ) + "\n" )
        sys.exit( 1 )

    def daemonize( self ):
        if not os.path.isdir( self.workpath ):
            self.perror( 'Workpath does not exist!', '' )

        try:
            pid = os.fork()

            if pid > 0:
                sys.exit( 0 )
        except OSError, err:
            self.perror( 'Fork #1 failed: {0}', err )

        try:
            pid = os.fork()

            if pid > 0:
                sys.exit( 0 )
        except OSError, err:
            self.perror( 'Fork #2 failed: {0}', err )

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open( os.devnull, 'r' )
        so = open( os.devnull, 'a+' )
        se = open( os.devnull, 'a+' )
        os.dup2( si.fileno(), sys.stdin.fileno() )
        os.dup2( so.fileno(), sys.stdout.fileno() )
        os.dup2( se.fileno(), sys.stderr.fileno() )

        atexit.register( os.remove, self.pidfile )
        pid = str( os.getpid() )

        fo = open( self.pidfile, 'w+' )
        fo.write( pid )
        fo.close()

        self.run()

    def run( self ):

        while true:
            time.sleep( 1 )

class DaemonCtl( object ):

    def __init__( self, daemon, cfg, workpath='/', foreground=False ):

        if not cfg.has_option( 'DEFAULT', 'pidfile' ):
            print 'You must have a pidfile variable in DEFAULT section'
            sys.exit( 1 )

        if not cfg.has_option( 'DEFAULT', 'logfile' ):
            print 'Variable logifile must be set in section DEFAULT'
            sys.exit( 1 )

        if not cfg.has_option( 'DEFAULT', 'loglevel' ):
            print 'Variable loglevel must be set in section DEFAULT'
            sys.exit( 1 )

        try:
            self.logging =  Logging( 
                                cfg.get_default( 'logfile' ),
                                cfg.getint( 'DEFAULT', 'loglevel' )
                            )
            self.logging.daemon = not foreground
        except ValueError:
            print 'Value of loglevel must be a integer'
            sys.exit( 1 )

        self.cfg = cfg
        self.log = self.logging.getLogger( 'DaemonCtl' )
        self.workpath = workpath
        self.foreground = foreground
        self.daemon = daemon
        self.pidfile = cfg.get_default( 'pidfile' )

        if foreground:
            self.log.info( 'starting in forground' )
        else:
            self.log.info( 'starting as daemon' )

    def start( self ):

        try:
            pf = open( self.pidfile, 'r' )
            pid = int( pf.read().strip() )
            pf.close()
        except IOError:
            pid = None

        if pid:
            print 'Pidfile {0} already exist. Daemon already running?'.format( self.pidfile )
            sys.exit( 1 )

        d = self.daemon( self.cfg, self.logging, self.pidfile, self.workpath )

        if self.foreground:
            d.run()
        else:
            d.daemonize()

    def stop( self ):

        try:
            pf = open( self.pidfile, 'r' )
            pid = int( pf.read().strip() )
            pf.close()
        except IOError:
            pid = None

        if not pid:
            print 'Pidfile {0} could not be found. Daemon not running?'.format( self.pidfile )
            return

        try:
            while True:
                os.kill( pid, signal.SIGTERM )
                time.sleep( 0.1 )
        except OSError, err:
            e = str( err.args )
            if e.find( "No such process" ) > 0:
                if os.path.exists( self.pidfile ):
                    os.remove( self.pidfile )
            else:
                print str( err.args )
                sys.exit( 1 )

    def restart( self ):
        self.stop()
        self.start()
