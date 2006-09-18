class FilterWheel(object):

    # properties
    position = 0

    # methods
    def setFilter(self, filter):
        pass

    # events
    @event
    def filterChanged(self, newFilter, lastFilter):
        pass

