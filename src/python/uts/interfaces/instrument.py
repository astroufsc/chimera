from uts.core.interface import Interface
from uts.core.event import event

class IInstrument (Interface):
    
    def __init__(self, manager):
        pass
        
    def init(self):
        pass
        
    def shutdown(self):
        pass

    @event
    def initComplete(self):
        pass
     
    @event    
    def shutdownComplete(self):
        pass
