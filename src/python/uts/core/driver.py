import threading

class Driver(object):

    def __init__(self, manager):

        self.manager = manager
        self.term = threading.Event()

    def init(self, config):
        pass

    def shutdown(self):
        self.term.set()

    def main(self):
        pass

