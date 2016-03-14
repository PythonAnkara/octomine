#-*- coding: utf-8 -*-

from queue import Queue
from threading import Thread


class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, tasks, crash):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.crash = crash
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print(e)
                pass
            finally:
                self.tasks.task_done()
                if self.crash:  break


class ThreadPool:
    """Pool of threads consuming tasks from a queue"""

    def __init__(self, num_threads, crash=False):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads): Worker(self.tasks, crash)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()
