#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

# chimera - observatory automation system
# Copyright (C) 2006-2007  P. Henrique Silva <henrique@astro.ufsc.br>

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.


#import chimera.core.log

import threading
import logging

from time import sleep

# Ensure booleans exist (not needed for Python 2.2.1 or higher)
try:
    True
except NameError:
    False = 0
    True = not False

#threading._VERBOSE = True

log = logging.getLogger(__name__)


class ThreadPool:

    """Flexible thread pool class.  Creates a pool of threads, then
    accepts tasks that will be dispatched to the next available
    thread."""

    def __init__(self, numThreads=10):
        """Initialize the thread pool with numThreads workers."""

        self.__threads = []
        self.__resizeLock = threading.Condition(threading.Lock())
        self.__taskLock = threading.Condition(threading.Lock())
        self.__tasks = []
        self.__isJoining = False
        self.setThreadCount(numThreads)

    def setThreadCount(self, newNumThreads):
        """
        External method to set the current pool size.  Acquires
        the resizing lock, then calls the internal version to do real
        work.
        """

        # Can't change the thread count if we're shutting down the pool!
        if self.__isJoining:
            return False

        self.__resizeLock.acquire()
        try:
            self.__setThreadCountNolock(newNumThreads)
        finally:
            self.__resizeLock.release()
        return True

    def __setThreadCountNolock(self, newNumThreads):
        """
        Set the current pool size, spawning or terminating threads
        if necessary.  Internal use only; assumes the resizing lock is
        held.
        """

        # If we need to grow the pool, do so
        while newNumThreads > len(self.__threads):
            newThread = ThreadPoolThread(self)
            self.__threads.append(newThread)
            newThread.start()
        # If we need to shrink the pool, do so
        while newNumThreads < len(self.__threads):
            self.__threads[0].goAway()
            del self.__threads[0]

    def getThreadCount(self):
        """Return the number of threads in the pool."""

        self.__resizeLock.acquire()
        try:
            return len(self.__threads)
        finally:
            self.__resizeLock.release()

    def queueTask(self, task, args=(), kwargs = {}, taskCallback=None):
        """
        Insert a task into the queue.  task must be callable;
        args and taskCallback can be None.
        """

        if self.__isJoining is True:
            return False
        if not callable(task):
            return False

        self.__taskLock.acquire()
        try:
            self.__tasks.append((task, args, kwargs, taskCallback))
            return True
        finally:
            self.__taskLock.release()

    def getNextTask(self):
        """
        Retrieve the next task from the task queue.  For use
        only by ThreadPoolThread objects contained in the pool.
        """

        self.__taskLock.acquire()
        try:
            if self.__tasks == []:
                return (None, None, None, None)
            else:
                return self.__tasks.pop(0)
        finally:
            self.__taskLock.release()

    def joinAll(self, waitForTasks=True, waitForThreads=True):
        """
        Clear the task queue and terminate all pooled threads,
        optionally allowing the tasks and threads to finish.
        """

        # Mark the pool as joining to prevent any more task queueing
        self.__isJoining = True

        # Wait for tasks to finish
        if waitForTasks:
            while self.__tasks != []:
                sleep(.1)

        # Tell all the threads to quit
        self.__resizeLock.acquire()
        try:
            self.__setThreadCountNolock(0)
            self.__isJoining = True

            # Wait until all threads have exited
            if waitForThreads:
                for t in self.__threads:
                    t.join()
                    del t

            # Reset the pool for potential reuse
            self.__isJoining = False
        finally:
            self.__resizeLock.release()


class ThreadPoolThread(threading.Thread):

    """
    Pooled thread class.
    """

    threadSleepTime = 0.1

    def __init__(self, pool):
        """
        Initialize the thread and remember the pool.
    """

        threading.Thread.__init__(self)
        self.__pool = pool
        self.__isDying = False

        self.setDaemon(True)

    def run(self):
        """
        Until told to quit, retrieve the next task and execute
        it, calling the callback if any.
        """

        while self.__isDying == False:
            cmd, args, kwargs, callback = self.__pool.getNextTask()

            # If there's nothing to do, just sleep a bit
            if cmd is None:
                sleep(ThreadPoolThread.threadSleepTime)
            else:

                log.debug("Running %s on thread %s" % (cmd, self.getName()))

                if callback is None:
                    cmd(*args, **kwargs)
                else:
                    callback(cmd(*args, **kwargs))

    def goAway(self):
        """ 
        Exit the run loop next time through.
        """

        self.__isDying = True
