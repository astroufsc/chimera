
from chimera.core.config import Config, OptionConversionException
from chimera.util.enum import Enum, EnumValue

from nose.tools import assert_raises

from types import StringType, IntType, FloatType, BooleanType


class TestConfig (object):

    def test_str (self):

        c = Config({"key_str": "value"})

        # valid
        for i in ("valid", 1, True, 1.0, object):
            assert c.__setitem__("key_str", i) != False, "%s (%s) is a valid str configuration" % (i, type(i))
            assert type(c.__getitem__("key_str")) == StringType, "should return str object"

        # invalid
        # any?

    def test_number (self):

        c = Config({"key_int": 10,
                    "key_float": 1.0})

        # valid
        for i in (1, 1.0, "1", "1.0", "-1", "-1.0", "   10  ", True):
            assert c.__setitem__("key_int", i) != False, "%s (%s) is a valid int configuration" % (i, type(i))
            assert type(c.__getitem__("key_int")) == IntType, "should return int object"
            
            assert c.__setitem__("key_float", i) != False, "%s (%s) is a valid float configuration" % (i, type(i))
            assert type(c.__getitem__("key_float")) == FloatType, "should return str object"            

        # invalid
        for i in (object, "a10", "1.a"):
            assert_raises (OptionConversionException, c.__setitem__, "key_int", i)
            assert_raises (OptionConversionException, c.__setitem__, "key_float", i)


    def test_bool (self):

        c = Config({"key_bool": True})

        # valid
        for i in (1, 1.0, 0, 0.0, "y", "Y", "yes", "YES", "n", "N", "no", "NO",
                  "on", "ON", "off", "OFF", "true", "TRUE", "false", "FALSE", True, False):
            
            # no assert because setitem returns the old and this can be False
            # we get errors if any set raises OptionConversionException
            c.__setitem__("key_bool", i)
            assert type(c.__getitem__("key_bool")) == BooleanType, "should return bool object"

        # invalid
        for i in (object, "ok", 10):
            assert_raises (OptionConversionException, c.__setitem__, "key_bool", i)


    def test_options (self):

        c = Config({"key_opt_int": [1, 2, 3],
                    "key_opt_float": [1, 2.0, 4.0],
                    "key_opt_bool": [1, False],
                    "key_opt_str": ["one", "two", "three"]})

        # valid
        for i in (1, 2, 3, True): # True == 1
            assert c.__setitem__("key_opt_int", i) != False, "%s (%s) is a valid configuration" % (i, type(i))
            assert type(c.__getitem__("key_opt_int")) == IntType, "should return int object"

        for i in ("one", "two", "three"):
            assert c.__setitem__("key_opt_str", i) != False, "%s (%s) is a valid configuration" % (i, type(i))
            assert type(c.__getitem__("key_opt_str")) == StringType, "should return str object"            


        # invalid
        for i in (4, 5, 6, "str", False):
            assert_raises (OptionConversionException, c.__setitem__, "key_opt_int", i)

        for i in ("four", "five", "six", 1, 2, 3, True, False):
            assert_raises (OptionConversionException, c.__setitem__, "key_opt_str", i)
            
        
    def test_range (self):

        c = Config({"key_range": (1, 10)}) # ranges are inclusive

        # valid
        for i in range(1, 11):
            assert c.__setitem__("key_range", i) != False, "%s (%s) is a valid configuration" % (i, type(i))
            assert type(c.__getitem__("key_range")) == IntType, "should return int object"

        # invalid
        for i in (0, 11, "str"):
            assert_raises (OptionConversionException, c.__setitem__, "key_range", i)


    def test_iter (self):

        d = {"device"       : "/dev/ttyS0",
             "ccd"          : ["imaging", "tracking"],
             "exp_time"     : (0.1, 6000.0),
             "shutter"      : ["open", "close", "leave"],
             "readout_aborted": True,
             "readout_mode" : 1,
             "date_format"  : "%d%m%y",
             "file_format"  : "$num-$observer-$date-%objname",
             "directory"    : "/home/someuser/images",
             "save_on_temp" : False,
             "seq_num"      : 1,
             "observer"     : "observer name",
             "obj_name"     : "object name"}

        c = Config(d)


        # len
        assert len(c) == len(d)

        # contains
        assert "device" in c
        assert "stuff" not in c

        # iter protocol
        assert c.keys() == c.keys()
        assert c.values() == c.values()        
        assert c.items() == c.items()

        # config using +=
        dd = {"new": 10}
        assert_raises(KeyError, c.__iadd__, dd)

        assert not "new" in c

        c += {"device":"foo"}
        assert c["device"] == "foo"
        assert isinstance (c, Config) # __iadd__ protocol, return self to allow daisy chaining

    def test_enum (self):

        Values = Enum("A_VALUE", "OTHER_VALUE")

        c = Config({"key_enum": Values.A_VALUE})

        # default
        assert c["key_enum"] == Values.A_VALUE

        # valid
        for i in Values:
            assert c.__setitem__("key_enum", i) != False, "%s (%s) is a valid enum configuration" % (i, type(i))
            assert type(c.__getitem__("key_enum")) == EnumValue, "should return EnumValue object"

        for i in ["A_VALUE", "OTHER_VALUE", "a_value", "other_value", "a_vAlUe", "other_value"]:
            assert c.__setitem__("key_enum", i) != False, "%s (%s) is a valid enum configuration" % (i, type(i))
            assert type(c.__getitem__("key_enum")) == EnumValue, "should return EnumValue object"

        # invalid
        assert_raises(KeyError, c.__getitem__, "WHATERVER")
        

        
