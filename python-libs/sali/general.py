# "SALI"
#
# Copyright (c) 2010 SARA Computing and Networking Services
#
#   $Id$

## Must be imported first
from __future__ import print_function

## Python modules
import os
import signal
import sys
import atexit
import logging
import time
from ConfigParser import SafeConfigParser
from ConfigParser import NoSectionError
from ConfigParser import NoOptionError

class Config( SafeConfigParser ):

    def __init__( self, cfgfile ):
        SafeConfigParser.__init__( self )
        self.readfp( open( cfgfile ) )

        if not self.has_section( 'bittorrent' ):
            print( 'Missing the bittorrent configuration in the given file, check the documentation!' )
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
            return self.get( 'DEFAULT', option )

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

        return True

    def do_updateimages( self ):
        try:
            if self.getboolean( 'update', 'enable_update' ):
                return True
        except NoOptionError:
            return False

        return True

    def do_monitor( self ):
        try:
            if self.getboolean( 'monitor', 'enabled' ):
                return True
        except NoOptionError:
            return False

        return True

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
            print( 'Configured level is incorrect choose 0 - 5' )

        self.level = self.LEVELS[ level ]

    def getLogger( self, name ):

        logger = logging.getLogger( name )
        logger.setLevel( logging.DEBUG )
    
        if not self.daemon:
            ch = logging.StreamHandler()

            if self.level == logging.DEBUG:
                ch.setLevel( logging.DEBUG )
            else:
                ch.setLevel( logging.INFO )

            ch.setFormatter( logging.Formatter( '%(name)-12s: %(levelname)-7s -- %(message)s' ) )
            logger.addHandler( ch ) 

        fh = logging.FileHandler( self.logfile )
        fh.setLevel( self.level )
        fh.setFormatter( logging.Formatter( '%(asctime)s - %(name)-12s - %(levelname)-7s - %(message)s' ) )
        logger.addHandler( fh )

        return logger

class Daemon:
    """A generic daemon class. Usage: subclass the daemon class and override the run() method.

        http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/"""

    daemon = False

    def __init__(self, pidfile):
        self.pidfile = pidfile
    
    def daemonize(self):
        """Deamonize class. UNIX double fork mechanism."""

        try: 
            self.log.debug( 'forking main process' )
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                self.log.debug( 'exiting first parent' )
                sys.exit(0) 
        except OSError as err: 
            self.log.critical( 'first fork failed: %s' % str( err ) )
            sys.stderr.write('fork #1 failed: {0}\n'.format(err))
            sys.exit(1)
    
        # decouple from parent environment
        self.log.debug( 'decouple from parent environment' )
        os.chdir('/') 
        os.setsid() 
        os.umask(0) 
    
        # do second fork
        try: 
            self.log.debug( 'forking again' )
            pid = os.fork() 
            if pid > 0:

                # exit from second parent
                self.log.debug( 'exiting from second parent' )
                sys.exit(0) 
        except OSError as err: 
            self.log.critical( 'second fork failed: %s' % str( err ) )
            sys.stderr.write('fork #2 failed: {0}\n'.format(err))
            sys.exit(1) 
    
        # redirect standard file descriptors
        self.log.debug( 'redirecting standard file descriptors' )
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
    
        # write pidfile
        self.log.debug( 'write pidfile' )
        atexit.register(self.delpid)

        pid = str(os.getpid())
        with open(self.pidfile,'w+') as f:
            f.write(pid + '\n')

        self.log.info( 'process has been daemonized' )
   
    def delpid(self):
        self.log.debug( 'removing pidfile' )
        os.remove(self.pidfile)

    def start( self ):
        """Start the daemon."""

        self.log.info( 'starting SaliServer' )

        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile,'r') as pf:

                pid = int(pf.read().strip())
        except IOError:
            pid = None
    
        if pid:
            message = "pidfile {0} already exist. " + \
                    "Daemon already running?\n"
            sys.stderr.write(message.format(self.pidfile))
            sys.exit(1)
        
        # Start the daemon
        if self.daemon:
            self.daemonize()

        self.run()

    def stop(self):
        """Stop the daemon."""

        self.log.info( 'stopping daemon' )
        # Get the pid from the pidfile
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None
    
        if not pid:
            self.log.critical( 'pidfile "%s" does not exist. Daemon not running?' % self.pidfile )
            message = "pidfile {0} does not exist. " + \
                    "Daemon not running?\n"
            sys.stderr.write(message.format(self.pidfile))
            return # not an error in a restart

        # Try killing the daemon process    
        self.log.debug( 'killing daemon' )
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            e = str(err.args)
            if e.find("No such process") > 0:
                self.log.error( 'could not locate process' )
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print( (str(err.args)) )
                sys.exit(1)

    def restart(self):
        """Restart the daemon."""
        self.log.info( 'restarting daemon' )
        self.stop()
        self.start()

    def run(self):
        """You should override this method when you subclass Daemon.
        
        It will be called after the process has been daemonized by 
        start() or restart()."""
