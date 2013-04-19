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

import atexit
import Queue
import threading
import types
import time
import sys

class Task( object ):

    def __init__( self, logging, args=None ):
        if args and type( args ) is not types.ListType:
            raise Exception( 'Must be a list' )

        self.args = args
        self.log = logging.getLogger( self.__class__.__name__ )
        atexit.register( self.exit )

    def run( self ):
        raise NotImplementedError( 'You must override run()' )

    def exit( self ):
        self.log.info( 'stopped' )

class StopTask( Exception ):
    pass

class Process( object ):

    queue = Queue.Queue()
    amount = 0

    def append( self, task ):
        if isinstance( task, Task ):
            self.amount += 1
            self.queue.put( task )
        else:
            print( 'given task is not an instance of Task' )
            sys.exit( 1 )

    def _run( self, thread, task ):
        
        while True:
            try:
                req = task.get()
                req.run()

                task.task_done()
            except StopTask:
                print( 'a child as stopped working, emergency exit' )
                os._exit( 1 )

    def run( self ):

        try:
            for i in range( self.amount ):
                worker = threading.Thread( target=self._run, args=( i, self.queue ) )
                worker.daemon = True
                worker.start()

            while True:
                time.sleep( 900 )
        except KeyboardInterrupt:
            print( 'stopping' )
            sys.exit( 1 )

        self.queue.join()
