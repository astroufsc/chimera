from uts.core.interface import Interface
from uts.core.event import event

class IFilterWheel(Interface):

    # properties
    position = 0

    # methods
    def setFilter(self, filter):
        pass

    # events
    @event
    def filterChanged(self, newFilter, lastFilter):
        pass

