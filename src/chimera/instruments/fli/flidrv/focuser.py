"""
 FLI.focuser.py

 Object-oriented interface for handling FLI (Finger Lakes Instrumentation) USB 
 focusers

 author:       Craig Wm. Versek, Yankee Environmental Systems 
 author_email: cwv@yesinc.com
"""

__author__ = 'Craig Wm. Versek'
__date__ = '2012-08-16'

from ctypes import byref, c_char, c_char_p, c_long, c_ubyte, c_double

from lib import FLILibrary, FLIError, FLIWarning, flidomain_t, flidev_t,\
    fliframe_t, FLIDOMAIN_USB, FLIDEVICE_FOCUSER,\
    FLI_TEMPERATURE_INTERNAL, FLI_TEMPERATURE_EXTERNAL

from device import USBDevice
###############################################################################
DEBUG = False

###############################################################################


class USBFocuser(USBDevice):
    # load the DLL
    _libfli = FLILibrary.getDll(debug=DEBUG)
    _domain = flidomain_t(FLIDOMAIN_USB | FLIDEVICE_FOCUSER)

    def __init__(self, dev_name, model):
        USBDevice.__init__(self, dev_name=dev_name, model=model)
        self.stepper_position = None
        extent = c_long()
        self._libfli.FLIGetFocuserExtent(self._dev, byref(extent))
        self.stepper_max_extent = extent.value

    def get_steps_remaining(self):
        steps = c_long()
        self._libfli.FLIGetStepsRemaining(self._dev, byref(steps))
        return steps.value

    def step_motor(self, steps, blocking=True, force=False):
        if not force:
            if self.get_steps_remaining() > 0:
                raise FLIError("""'step_motor' command ignored because motor is still moving! Use force=True to bypass."""
                               )
            if self.stepper_position is None:
                self.get_stepper_position()
            end_pos = self.stepper_position + steps
            if end_pos > self.stepper_max_extent:
                raise FLIError("""'step_motor' command ignored because user tried to drive stepper motor to end position %d, which is beyond its max exent, %d. Use force=True to bypass"""
                               % (end_pos, self.stepper_max_extent)
                               )
        if blocking:
            self._libfli.FLIStepMotor(self._dev, c_long(steps))
            return self.get_stepper_position()
        else:
            self.stepper_position = None
            self._libfli.FLIStepMotorAsync(self._dev, c_long(steps))
            return None

    def get_stepper_position(self):
        pos = c_long()
        self._libfli.FLIGetStepperPosition(self._dev, byref(pos))
        self.stepper_position = pos.value
        return pos.value

    def home_focuser(self):
        self._libfli.FLIHomeFocuser(self._dev)
        return self.get_stepper_position()

    def read_internal_temperature(self):
        temp = c_double()
        self._libfli.FLIReadTemperature(
            self._dev, FLI_TEMPERATURE_INTERNAL, byref(temp))
        return temp.value

    def read_external_temperature(self):
        temp = c_double()
        self._libfli.FLIReadTemperature(
            self._dev, FLI_TEMPERATURE_EXTERNAL, byref(temp))
        return temp.value


###############################################################################
#  TEST CODE
###############################################################################
if __name__ == "__main__":
    focs = USBFocuser.find_devices()
    foc0 = focs[0]
