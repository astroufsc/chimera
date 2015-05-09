import logging

from chimera.core.lock import lock
from chimera.instruments.filterwheel import FilterWheelBase
from chimera.instruments.fli.flidrv.filter_wheel import USBFilterWheel

__config__ = dict(device="/dev/ttyS0",
                  filter_wheel_model="",
                  filters="U B V R I")

log = logging.getLogger(__name__)


class FliFilter(FilterWheelBase):
    """
    FLI USB filterwheel device.

    A Chimera tailored device class for FInger Lakes Instruments devices. This
    should be imported by the corresponding Camera class in order to be used.
    UNTESTED.
    """
    # NOTE: assuming 1-indexed positions returned by driver; correct
    # accordingly.
    def __init__(self):
        FilterWheelBase.__init__(self)
        # NOTE: there may be more than 1 wheel.
        fws = USBFiletrWheel.find_devices()
        if len(fws) == 0:
            self.log.critical("No filter wheels found!")
            return None
        # Arbitrarily assume only one
        self.fw = fws[0]
        self['filter_wheel_model'] = self.fw.model

    @lock
    def setFilter(self, filter):
        USBFilterWheel.set_filter_pos(self['filters'].index(filter))

    @lock
    def getFilter(self):
        return self['filters'][USBFilterWheel.get_filter_pos()]

    def getFilters(self):
        return self['filters']

    def getMetadata(self, request):
        return [('FWHEEL', str(self['filter_wheel_model']), 'FilterWheel Model'),
                ('FILTER', str(self.getFilter()),
                 'Filter used for this observation')]
