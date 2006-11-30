from uts.core.interface import Interface
from uts.core.event import event

class ILifeCycle (Interface):

    """
    Basic interface implemented by every device on the system. This
    interface provides basic life-cycle management and main loop control.

    """

    def __init__(self, manager):
        """
        Do object initialization.

        Constructor should only do basic initialization. Shouldn't
        even 'touch' any hardware, open files or sockets. Constructor
        is called by L{Manager}.

        @note: Runs on the Manager's thread.
        @warning: This method must not block, so be a good boy/girl.
        
        @param manager: a L{Manager} instance
        @type manager: L{Manager}
        """
        
    def init(self, config):
        """
        Do device initialization. Open files, access drivers and
        sockets. This method it's called by Manager, just after the constructor.

        @param config: configuration dictionary.
        @type config: dict

        @note: Runs on the L{Manager} thread.
        @warning: This method must not block, so be a good boy/girl.
        """
        
    def shutdown(self):
        """
        Cleanup {init} actions.

        {shutdown} it's called by Manager when Manager is diying or
        programatically at any time (to remove an Instrument during
        system lifetime).

        @note: Runs on the Manager thread.
        @warning: This method must not block, so be a good boy/girl.
        """

    def main(self):
        """
        Main control method. Implementeers could use this method to
        implement control loop functions. See L{Instrument}.

        @note: This method runs on their own thread.
        """

    @event
    def initComplete(self):
        """
        """
     
    @event    
    def shutdownComplete(self):
        """
        """
