import threading

from uts.interfaces.driver import IDriver

class Driver(IDriver):

    def __init__(self, manager):

        self.manager = manager
        self.term = threading.Event()
        
    def init(self):
        pass

    def shutdown(self):
        self.term.set()

    def main(self):
        pass

