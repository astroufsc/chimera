import threading

class Controller(object):

    def __init__(self, manager, location):

        self.manager = manager
        self.location = location
        self.term = threading.Event()

    def main(self):
        pass

