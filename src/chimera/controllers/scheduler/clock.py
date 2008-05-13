
from chimera.util.enum import Enum

import threading


"""
Epoch defines the current 'state of the day'. We only care about day
(past sunrise twilight), night (past sunset twilight) and during
repective twilights. Clock wakeup Machine after each transition.
"""
Epoch = Enum("DAY", "SUNSET_TWILIGHT", "NIGHT", "SUNRISE_TWILIGHT")


class Now (object):

    __timesstamp = 0
    __epoch      = Epoch.NIGHT
    __date       = None
    __time       = None
    __datetime   = None
    __jd         = None
    __mjd        = None

    
    timestamp  = property(lambda self: self.__timestamp, lambda self, value: setattr(self, '__timestamp', value))
    epoch      = property(lambda self: self.__epoch    , lambda self, value: setattr(self, '__epoch'    , value))
    date       = property(lambda self: self.__date     , lambda self, value: setattr(self, '__date'     , value))
    time       = property(lambda self: self.__time     , lambda self, value: setattr(self, '__time'     , value))
    datetime   = property(lambda self: self.__datetime , lambda self, value: setattr(self, '__datetime' , value))
    jd         = property(lambda self: self.__jd       , lambda self, value: setattr(self, '__jd'       , value))
    mjd        = property(lambda self: self.__mjd      , lambda self, value: setattr(self, '__mjd'      , value))


__instance = None

def Clock (*args, **kwargs):
    global __instance
    if not __instance:
        __instance = _Clock(*args, **kwargs)
    return __instance
        
class _Clock (object):

    """
    Clock uses Timer class to keep track of current day events and to
    update itself when next day cames in. When some event happens, it
    wakeups the Machine and let him do the rest.
    """

    def __init__ (self, machine):

        self.machine = machine
        self.today = None

        # store current day computes sunrise, sunset and twilight dates
        self._cache = {}

        # setup timer
        #def wakeup():
        #    self.machine.wakeup()
            
        #timer = threading.Timer(30, wakeup)
        #timer.start()

    def now (self):
        now = Now()
        return now
