import logging

from types import (IntType, FloatType, StringType, LongType,
                   DictType, TupleType, ListType, BooleanType)


class OptionConversionException (Exception):
    pass


class Option (object):

    def __init__ (self, name, value, checker):

        self._name = name
        self._value = value
        self._default = value
        self._checker = checker

    def set (self, value):
        
        try:
            self._value = self._checker.check(value)

        except OptionConversionException, e:
            self._value = self._default
            
            logging.debug ("Error setting %s: %s." % (self._name, str (e)))


    def get (self):
        return self._value


class Checker (object):

    def check (self, value):
        pass


class IgnoreChecker (Checker):

    def __init__ (self):
        Checker.__init__ (self)

    def check (self, value):
        return value


class IntChecker (Checker):

    def __init__ (self):
        Checker.__init__ (self)

    def check (self, value):
        # we MUST return an int or raise OptionConversionException
        # if we can't get one from "value"

        # simple case
        if type (value) in (IntType, FloatType):
            return int (value)

        if type (value) == StringType:

            # try to convert to int
            try:
                tmp = int (value)
                return tmp
            except ValueError:
                # couldn't convert, nothing to do
                raise OptionConversionException ("couldn't convert '%s' to int value." % value)

        # any other type are sillently ignored
        raise OptionConversionException ("couldn't convert %s to int." % str (type (value)))


class FloatChecker (Checker):

    def __init__ (self):
        Checker.__init__ (self)

    def check (self, value):
        # we MUST return an float or raise OptionConversionException
        # if we can't get one from "value"

        # simple case
        if type (value) in (FloatType, IntType):
            return float (value)

        if type (value) == StringType:

            # try to convert to int
            try:
                tmp = float (value)
                return tmp
            except ValueError:
                # couldn't convert, nothing to do
                raise OptionConversionException ("couldn't convert '%s' to float value." % value)

        # any other type are sillently ignored
        raise OptionConversionException ("couldn't convert %s to float." % str (type (value)))


class StringChecker (Checker):

    def __init__ (self):
        Checker.__init__ (self)

    def check (self, value):
        # we MUST return an str or raise OptionConversionException
        # if we can't get one from "value"

        # simple case (nearly everything can be converted to str, just cross fingers and convert!)
        return str (value)

class BoolChecker (Checker):

    def __init__ (self):
        Checker.__init__ (self)

        self._trueValues = ["true", "yes", "y", "on", "1"]
        self._falseValues = ["false", "no", "n", "off", "0"]
        self._truthTable =  self._trueValues + self._falseValues

    def check (self, value):
        # we MUST return an bool or raise OptionConversionException
        # if we can't get one from "value"

        if type (value) == BooleanType:
            return value

        # only accept 0 and 1 as valid booleans...
        # cause a lot of problems in OptionChecker accept the same as python truth tables assume
        if type (value) in (IntType, FloatType):
    
            if value == 1:
                return True

            if value == 0:
                return False

        if type (value) == StringType:

            value = value.strip().lower()

            if value in self._truthTable:
                return value in self._trueValues

            raise OptionConversionException ("couldn't convert '%s' to bool." % value)

        # any other type, raise exception
        raise OptionConversionException ("couldn't convert %s to bool." % str (type (value)))


class OptionsChecker (Checker):

    def __init__ (self, options):
        Checker.__init__ (self)

        self._options = self._readOptions (options)

    def _readOptions (self, opt):

        # options = [ {"value": value, "checker", checker}, ...]
        options = []
        
        for value in opt:

            if type (value) == IntType:
                options.append ({"value": value,
                                 "checker": IntChecker ()})
                continue

            if type (value) == FloatType:
                options.append ({"value": value,
                                 "checker": FloatChecker ()})
                continue

            if type (value) == StringType:
                options.append ({"value": value,
                                 "checker": StringChecker ()})
                continue

            if type (value) == BooleanType:
                options.append ({"value": value,
                                 "checker": BoolChecker ()})
                continue

        return options

    def check (self, value):

        for option in self._options:

            try:
                tmp = option["checker"].check (value)
                
                if tmp == option["value"]:
                    return option["value"]
                else:
                    continue

            except OptionConversionException, e:

                continue

        raise OptionConversionException ("'%s' isn't a valid option." % str (value))


class RangeChecker (Checker):

    def __init__ (self, value):
        Checker.__init__ (self)

        self._min = value[0]
        self._max = value[1]

        if type (value[0]) == FloatType:
            self._checker = FloatChecker ()

        else:
            self._checker = IntChecker ()
           

    def check (self, value):

        try:
            tmp = self._checker.check (value)

        except OptionConversionException, e:

            raise OptionConversionException ("'%s' isn't a valid option." % str (value))

        else:

            if (tmp >= self._min) and (tmp <= self._max):
                return tmp
            else:
                raise OptionConversionException ("'%s' it's outside valid limits (%f <= x <= %f." % (str (value),
                                                                                                     self._min,
                                                                                                     self._max))


class Config (object):

    def __init__ (self, options):
        object.__setattr__ (self, '_options', self._readOptions (options))

    def _readOptions (self, opt):

        options = {}

        for name, value in opt.items ():

            if type (value) == IntType:
                options[name] = Option (name, value, IntChecker ())
                continue

            if type (value) == FloatType:
                options[name] = Option (name, value, FloatChecker ())
                continue

            if type (value) == StringType:
                options[name] = Option (name, value, StringChecker ())
                continue

            if type (value) == BooleanType:
                options[name] = Option (name, value, BoolChecker ())
                continue

            # FIXME: for list and tuple we use the first element as default option
            #        there is no way to specify other default for this types
            if type (value) == ListType:
                options[name] = Option (name, value[0], OptionsChecker (value))
                continue

            if type (value) == TupleType:
                options[name] = Option (name, value[0], RangeChecker (value))
                continue

        return options

    def __contains__ (self, name):
        return name in self._options

    def __len__ (self):
        return len(self._options)

    def __getitem__ (self, name):

        if type (name) != StringType:
            raise TypeError

        if name in self:
            return self._options[name].get ()

        else:
            logging.debug ("invalid option ('%s')." % name)
            raise KeyError

    def __setitem__ (self, name, value):

        # if value exists, run template checker and set _config
        if name in self:
            self._options[name].set (value)

        # rant about invalid option
        else:
            logging.debug ("invalid option ('%s')." % name)
            raise KeyError
       

    def __iter__ (self):

        return self.iterkeys()

    def iterkeys (self):

        return self._options.__iter__()

    def itervalues (self):

        for name in self._options:
            yield self._options[name].get ()

    def iteritems (self):

        for name in self._options:
            yield (name, self._options[name].get ())

    def keys (self):
        return [key for key in self.iterkeys()]

    def values (self):
        return [value for value in self.itervalues()]

    def items (self):
        return [(name, value) for name, value in self.iteritems()]

    def __iadd__ (self, other):

        if type (other) not in (Config, DictType):
            return

        for name, value in other.items():
            self[name] = value

        return self

    def __getattr__ (self, name):

        if name in self:
            return self[name]

        else:
            logging.debug ("invalid option ('%s')." % name)
            raise AttributeError

    def __setattr__ (self, name, value):

        if name in self:
            self[name] = value
        else:
            logging.debug ("invalid option ('%s')." % name)
            raise AttributeError

    
if __name__ == '__main__':

    options = {
        "device"	: "/dev/ttyS0",
        "ccd"		: ["imaging", "tracking"],
        "exp_time"	: (0.1, 6000.0),
        "shutter"	: ["open", "close", "leave"],
        "readout_aborted": True,
        "readout_mode"	: 1,
        "date_format"	: "%d%m%y",
        "file_format"	: "$num-$observer-$date-%objname",
        "directory"	: "/home/someuser/images",
        "save_on_temp"	: False,
        "seq_num"	: 1,
        "observer"	: "observer name",
        "obj_name"	: "object name"}

    c = Config (options)
