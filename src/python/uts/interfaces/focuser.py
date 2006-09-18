class Focuser(object):

    # properties
    position = 0.0
    type = ""
    maxIncrement = 0
    maxStep = 0
    tepSize = 0
    temperature = 0

    # methods
    def abortMove(self):
        pass

    def move(self, position):
        pass

    # events
    @event
    def focusChanged(self, newPosition, lastPosition):
        pass

