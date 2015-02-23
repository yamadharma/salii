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

import time
import sys
import signal
from multiprocessing import Process
from multiprocessing import Queue

from sali.server.web import web_app
from sali.server.imager import imager_run

def processor(cls, job_queue, result_queue):
    '''It is ugly to pass the class object, but I can't use this function within class with pickling'''
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while not job_queue.empty():
        try:
            job = job_queue.get(block=False)
            result_queue.put(job(cls.cmn))
        except Exception as err:
            cls.logger.critical('a thread has raised an exception: %s with error %s' % (str(job), str(err)))
            cls.exit()

class Server(object):
    '''The main Server object which is used to startup the different processes'''

    def __init__(self, cmn):
        self.cmn    = cmn
        self.logger = cmn.get_logger(__name__ + '.Server')

        ## Check if there is something enabled
        if not self.cmn.cfg.getboolean('daemons', 'web') and not self.cmn.cfg.getboolean('daemons', 'imager'): 
            self.logger.info('none of the daemons has been enabled in the configuration section [daemons]')
            sys.exit(0)

        job_length      = 0
        job_queue       = Queue()
        result_queue    = Queue()

        ## Let's fetch all types of signals for termination
        signallist = (signal.SIGINT, signal.SIGQUIT, signal.SIGABRT, signal.SIGPIPE, signal.SIGALRM, signal.SIGTERM)
        for sig in signallist:
            signal.signal(sig, self.signal_handler)

        ## Add the different processes to the job_queue
        if self.cmn.cfg.getboolean('daemons', 'web'):
            job_length += 1
            job_queue.put(web_app)
        if self.cmn.cfg.getboolean('daemons', 'imager'):
            job_length += 1
            job_queue.put(imager_run)

        ## Create and start the workers
        self.workers = list()
        for i in xrange(job_length):
            tmp = Process(target=processor, args=(self, job_queue, result_queue))
            tmp.start()
            self.workers.append(tmp)

        try:
            ## Keep checking if all workers are busy! (they must)
            while True:
                for worker in self.workers:
                    ## If a worker is not alive, then something is wrong, so kill everything
                    if not worker.is_alive():
                        self.logger.critical('a child process has stopped working, killing sali')
                        self.exit()
                time.sleep(0.1)
        ## Allow control-c interrupt
        except KeyboardInterrupt:
            self.logger.info('caught control-c exiting')
            self.exit(0)
        ## Any other expcetion must be caught
        except Exception as err:
            self.logger.critical('caught a critical exception: %s' % err)
            self.exit()

    def signal_handler(self, _signo=0, _stack_frame=None):
        self.logger.debug('Caught a signal %d' % _signo)
        for worker in self.workers:
            worker.terminate()
        sys.exit(0)

    def exit(self, exitcode=1):
        ## loop through all workers and terminate them
        for worker in self.workers:
            worker.terminate()
        ## and finally the main process
        sys.exit(exitcode)
