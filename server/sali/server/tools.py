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
# Copyright 2010-2013 SURFsara

import warnings
warnings.filterwarnings( 'ignore', category=DeprecationWarning )

import os
import subprocess
import operator
import shutil
import re

from SaliBitTornado.BT1.makemetafile import make_meta_file

class CreateImage( object ):

    def __init__( self, logger, cfg, cli=False ):
        self.cfg = cfg
        self.log = logger.getLogger( self.__class__.__name__, cli=cli )
        self.taropts = [ '-p', '-c', '-f' ]
        self.tarballext = 'tar'
        self.meta_exts = {
            'torrent': self.create_torrent,
        }

        ## Check if we have an imagedir
        if not cfg.has_option( 'update', 'imagedir' ) or not os.path.exists( cfg.get( 'update', 'imagedir' ) ):
            self.log.critical( 'could not locate imagedir, check your configuration' )
            sys.exit( 1 )
        else:
            self.imagedir = cfg.get( 'update', 'imagedir' )

        ## Check if we have a torrentsdir
        if not cfg.has_option( 'bittorrent', 'torrentsdir' ) or not os.path.exists( cfg.get( 'bittorrent', 'torrentsdir' ) ):
            self.log.critical( 'could not locate torrentsdir, check your configuration' )
            sys.exit( 1 )
        else:
            self.torrentsdir = cfg.get( 'bittorrent', 'torrentsdir' )

        ## Check if we have a trackeradress
        if not cfg.has_option( 'update', 'trackeradress' ):
            self.log.critical( 'trackeradress must be configured' )
            sys.exit( 1 )
        else:
            self.trackeradress = cfg.get( 'update', 'trackeradress' )

        ## Is a tarcommand been set, else let's try to find it! 
        if not cfg.has_option( 'update', 'tarcommand' ) or not os.path.exists( cfg.get( 'update', 'tarcommand' ) ):
            self.taropts.insert( 0, self.find_tar() )
        elif not os.path.exists( cfg.get( 'update', 'tarcommand' ) ):
            self.log.critical( 'could not locate tarcommand, check your config' )
            sys.exit( 1 )
        else:
            self.taropts.insert( 0, cfg.get( 'update', 'tarcommand' ) )

        if cfg.has_option( 'update', 'compress' ):
            try:
                if cfg.getboolean( 'update', 'compress' ):
                    self.tarballext = 'tar.gz'
                    self.taropts.insert( 1, '-z' )
            except ValueError:
                pass

    def space( self, level=0 ):
        return " " * level

    def get_interfaces(self):
    
        p = subprocess.Popen(
            'ip addr',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )

        stdout, stderr = p.communicate()

        if p.returncode != 0:
            self.log.critical('Could not fetch interfaces')

        ## A simple 
        in_int = None
        addresses = dict()
        for line in stdout.splitlines():
            if re.search(r'^[0-9]+:.+', line):
                int_name = line.split()[1][:-1]
                if int_name in ['lo',]:
                    continue
                in_int = int_name
            elif in_int:
                if line.strip().split()[0] == 'inet':
                    ip = line.strip().split()[1].split('/')[0]
                    if not addresses.has_key(int_name):
                        addresses[int_name] = ip
                        int_name = None
                    else:
                        print "Duplicate interface name found!"                   
        return addresses

    def display_torrent( self, complete ):
        percent = operator.mul( complete, 100 )

        if percent >= 100:
            self.log.info( '%s torrent file has been created' % self.space( 6 ) )

    def create_torrent( self, targetfile ):

        trackers = self.trackeradress.split(',')

        if len(trackers) == 1:
            URL = trackers[0]
            if re.search(r'0.0.0.0', URL):
                trackers = list()
                for intf, ip in self.get_interfaces().items():
                    trackers.append(re.sub(r'0.0.0.0', ip, URL)) 

        if len(trackers) > 1:
            params = dict( 
                target='%s.torrent' % targetfile,
                announce_list="|".join(trackers[1:]),
            )
        else:
            params = dict( 
                target='%s.torrent' % targetfile
            )

        make_meta_file( targetfile, trackers[0], progress=self.display_torrent, params=params ) 

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
                        self.log.warning( '%s%s' % ( self.space( 6 ), line.strip() ) )

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
