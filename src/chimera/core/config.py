# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>


from types import NoneType

from chimera.core.exceptions import OptionConversionException

from chimera.util.coord import Coord
from chimera.util.enum import Enum
from chimera.util.position import Position

import logging

log = logging.getLogger(__name__)


class Option(object):

    def __init__(self, name, value, checker):

        self._name = name
        self._value = value
        self._default = value
        self._checker = checker

    def __repr__(self):
        return f"<Option {self._name}={self._value}>"

    def set(self, value):

        try:
            old_value = self._value

            self._value = self._checker.check(value)

            return old_value
        except OptionConversionException as e:
            log.debug(f"Error setting {self._name}: {str(e)}.")
            raise e

    def get(self):
        return self._value


class Checker(object):

    def check(self, value):
        pass


class IgnoreChecker(Checker):

    def __init__(self):
        Checker.__init__(self)

    def check(self, value):
        return value


class IntChecker(Checker):

    def __init__(self):
        Checker.__init__(self)

    def check(self, value):
        # we MUST return an int or raise OptionConversionException
        # if we can't get one from "value"

        # simple case
        if isinstance(value, (int, float, bool)):
            return int(value)

        if isinstance(value, str):
            # try to convert to int (use float first and then cast (loosely)
            try:
                tmp = float(value)
                tmp = int(tmp)
                return tmp
            except ValueError:
                # couldn't convert, nothing to do
                raise OptionConversionException(
                    f"couldn't convert '{value}' to int value."
                )

        raise OptionConversionException(
            f"couldn't convert '{str(type(value))}' to int."
        )


class FloatChecker(Checker):

    def __init__(self):
        Checker.__init__(self)

    def check(self, value):
        # we MUST return an float or raise OptionConversionException
        # if we can't get one from "value"

        # simple case
        if isinstance(value, (float, int, bool)):
            return float(value)

        if isinstance(value, str):

            # try to convert to int
            try:
                tmp = float(value)
                return tmp
            except ValueError:
                # couldn't convert, nothing to do
                raise OptionConversionException(
                    f"couldn't convert '{value}' to float value."
                )

        raise OptionConversionException(
            f"couldn't convert {str(type(value))} to float."
        )


class StringChecker(Checker):

    def __init__(self):
        Checker.__init__(self)

    def check(self, value):
        # we MUST return an str or raise OptionConversionException
        # if we can't get one from "value"

        # simple case (nearly everything can be converted to str, just cross
        # fingers and convert!)
        return str(value)


class NoneChecker(Checker):

    def __init__(self):
        Checker.__init__(self)

    def check(self, value):
        # Just return the None value.
        return value


class BoolChecker(Checker):

    def __init__(self):
        Checker.__init__(self)

        self._true_values = ["true", "yes", "y", "on", "1"]
        self._false_values = ["false", "no", "n", "off", "0"]
        self._truth_table = self._true_values + self._false_values

    def check(self, value):
        # we MUST return an bool or raise OptionConversionException
        # if we can't get one from "value"

        if isinstance(value, bool):
            return value

        # only accept 0 and 1 as valid booleans...
        # cause a lot of problems in OptionChecker accept the same as python
        # truth tables assume
        if isinstance(value, (int, float)):

            if value == 1:
                return True

            if value == 0:
                return False

        if isinstance(value, str):

            value = value.strip().lower()

            if value in self._truth_table:
                return value in self._true_values

            raise OptionConversionException(f"couldn't convert '{value}' to bool.")

        # any other type, raise exception
        raise OptionConversionException(f"couldn't convert {str(type(value))} to bool.")


class OptionsChecker(Checker):

    def __init__(self, options):
        Checker.__init__(self)

        self._options = self._read_options(options)

    def _read_options(self, opt):

        # options = [ {"value": value, "checker", checker}, ...]
        options = []

        for value in opt:

            if isinstance(value, int):
                options.append({"value": value, "checker": IntChecker()})
                continue

            if isinstance(value, float):
                options.append({"value": value, "checker": FloatChecker()})
                continue

            if isinstance(value, str):
                options.append({"value": value, "checker": StringChecker()})
                continue

            if isinstance(value, bool):
                options.append({"value": value, "checker": BoolChecker()})
                continue

        return options

    def check(self, value):

        for option in self._options:

            try:
                tmp = option["checker"].check(value)

                if tmp == option["value"]:
                    return option["value"]
                else:
                    continue

            except OptionConversionException:
                continue

        raise OptionConversionException(f"'{str(value)}' isn't a valid option.")


class RangeChecker(Checker):

    def __init__(self, value):
        Checker.__init__(self)

        self._min = value[0]
        self._max = value[1]

        if isinstance(value[0], float):
            self._checker = FloatChecker()

        else:
            self._checker = IntChecker()

    def check(self, value):

        try:
            tmp = self._checker.check(value)
        except OptionConversionException:
            raise OptionConversionException(f"'{str(value)}' isn't a valid option.")

        else:

            # inclusive
            if (tmp >= self._min) and (tmp <= self._max):
                return tmp
            else:
                raise OptionConversionException(
                    f"'{str(value)}' it's outside valid limits ({self._min:f} <= x <= {self._max:f}."
                )


class EnumChecker(Checker):

    def __init__(self, value):
        Checker.__init__(self)

        self.enum_type = value.enumtype

    def check(self, value):

        if isinstance(value, Enum):
            if value in self.enum_type:
                return value

        if isinstance(value, str):
            ret = [v for v in self.enum_type if str(v).upper() == value.upper()]
            if ret:
                return ret[0]

        raise OptionConversionException(
            f"invalid enum value {value}. not a {str(self.enum_type)} enum."
        )


class CoordOption(Option):

    def __init__(self, name, value, checker):
        Option.__init__(self, name, value, checker)

        self._state = value.state

    def set(self, value):
        try:
            old_value = self._value
            self._value = self._checker.check(value, self._state)
            return old_value
        except OptionConversionException as e:
            log.debug(f"Error setting {self._name}: {str(e)}.")
            raise e


class CoordChecker(Checker):

    def __init__(self, value):
        Checker.__init__(self)

    def check(self, value, state=None):

        if not isinstance(value, Coord):
            try:
                return Coord.from_state(value, state)
            except ValueError:
                pass

        # any other type is ignored
        raise OptionConversionException(f"invalid coord value {value}.")


class PositionOption(Option):

    def __init__(self, name, value, checker):
        Option.__init__(self, name, value, checker)

        self._system = value.system
        self._epoch = value.epoch

    def set(self, value):
        try:
            old_value = self._value
            self._value = self._checker.check(value, self._system, self._epoch)
            return old_value
        except OptionConversionException as e:
            log.debug(f"Error setting {self._name}: {str(e)}.")
            raise e


# FIXME: check and convert positions


class PositionChecker(Checker):

    def __init__(self, value):
        Checker.__init__(self)

    def check(self, value, state=None):
        return value


class Config(object):

    def __init__(self, obj):

        if isinstance(obj, dict):
            self._options = self._read_options(obj)
        else:
            self._options = self._read_options(obj.__config__)

    def _read_options(self, opt):

        options = {}

        for name, value in list(opt.items()):

            if isinstance(value, int):
                options[name] = Option(name, value, IntChecker())
                continue

            if isinstance(value, float):
                options[name] = Option(name, value, FloatChecker())
                continue

            if isinstance(value, str):
                options[name] = Option(name, value, StringChecker())
                continue

            if isinstance(value, bool):
                options[name] = Option(name, value, BoolChecker())
                continue

            if isinstance(value, NoneType):
                options[name] = Option(name, value, NoneChecker())
                continue

            # For list and tuple we use the first element as default option.
            # If the list/tuple is empty, its value will be assigned None.
            if isinstance(value, list):
                if len(value) > 0:
                    options[name] = Option(name, value[0], OptionsChecker(value))
                else:
                    options[name] = Option(name, None, NoneChecker())
                continue

            if isinstance(value, tuple):
                if len(value) > 0:
                    options[name] = Option(name, value[0], RangeChecker(value))
                else:
                    options[name] = Option(name, None, NoneChecker())
                continue

            if isinstance(value, Enum):
                options[name] = Option(name, value, EnumChecker(value))
                continue

            # special Coord type, remember which state create the
            # option to allow the use of the right constructor when
            # checking new values
            if isinstance(value, Coord):
                options[name] = CoordOption(name, value, CoordChecker(value))
                continue

            if isinstance(value, Position):
                options[name] = PositionOption(name, value, PositionChecker(value))
                continue

            raise ValueError(f"Invalid option type: {type(value)}.")

        return options

    def __contains__(self, name):
        return name in self._options

    def __len__(self):
        return len(self._options)

    def __getitem__(self, name):

        if not isinstance(name, str):
            raise TypeError

        if name in self:
            return self._options[name].get()

        else:
            raise KeyError(f"invalid option: {name}.")

    def __setitem__(self, name, value):

        # if value exists, run template checker and set _config
        if name in self:
            return self._options[name].set(value)

        # rant about invalid option
        else:
            raise KeyError(f"invalid option: {name}.")

    def __iter__(self):
        return iter(self.keys())

    def iter_keys(self):
        return self._options.__iter__()

    def iter_values(self):
        for name in self._options:
            yield self._options[name].get()

    def iter_items(self):
        for name in self._options:
            yield (name, self._options[name].get())

    def keys(self):
        return [key for key in self._options.keys()]

    def values(self):
        return [value for value in self._options.values()]

    def items(self):
        return [(name, value) for name, value in self._options.items()]

    def __iadd__(self, other):

        if isinstance(other, (Config, dict)):
            return self

        if isinstance(other, dict):
            other = Config(other)

        for name, value in list(other._options.items()):
            if name not in self._options:
                raise KeyError(f"invalid option: {name}")

            self._options[name] = value

        return self
