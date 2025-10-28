# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from chimera.core.interface import Interface


__all__ = ["ILifeCycle"]


class ILifeCycle(Interface):
    """
    Basic interface implemented by every device on the system. This
    interface provides basic life-cycle management and main loop control.

    """

    def __init__(self):
        """
        Do object initialization.

        Constructor should only do basic initialization. Shouldn't
        even 'touch' any hardware, open files or sockets. Constructor
        is called by L{Manager}.

        @note: Runs on the Manager's thread.
        @warning: This method must not block, so be a good boy/girl.
        """

    def __start__(self):
        """
        Do device initialization. Open files, sockets, etc. This
        method it's called by Manager, just after the constructor.

        @note: Runs on the L{Manager} thread.
        @warning: This method must not block, so be a good boy/girl.
        """

    def __stop__(self):
        """
        Cleanup {__start__} actions.

        {__stop__} it's called by Manager when Manager is dying or
        programatically at any time (to remove an Instrument during
        system lifetime).

        @note: Runs on the Manager thread.
        @warning: This method must not block, so be a good boy/girl.
        """

    def __main__(self):
        """
        Main control method. Implementers could use this method to
        implement control loop functions.

        @note: This method runs on their own thread.
        """

    def get_state(self):
        """
        Get the current state of the object as a L{State} enum.

        @see: L{State} for possible values.
        """

    def __setstate__(self, state):
        """
        Internally used function to set the current state of the object.

        @see: L{State} for possible values.
        """

    def get_location(self) -> str:
        """
        Get the current L{Location} where the object is deployed.
        """
        ...

    def get_proxy(self, url: str | None = None):
        """
        Get a Proxy for this object (useful for callbacks)
        """

    def get_metadata(self, data):
        """
        Get metadata about this object to be added to other objects
        (like images) metadata.

        @param data: The data to be processed by this object. Metadata
        handlers could use this data as a source of extra metadata
        information.
        @type data: Whatever the caller want to pass, object doesn't need to use it.

        @return: Current object metadata to be added to data metadata.
        @rtype: dict
        """
