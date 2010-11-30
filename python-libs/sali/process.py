
import atexit
import Queue
import threading
import types
import time

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
