
from chimera.core.location   import Location
from chimera.core.exceptions import InvalidLocationException

from nose.tools import assert_raises

from types import StringType


class TestLocation (object):

    def test_create (self):

        # simple strings
        l = Location('/Class/name?option1=value1,option2=value2')
        assert l

        assert l.host == None
        assert l.port == None
        assert l.cls == "Class"
        assert l.name == "name"
        assert l.config == dict(option1="value1", option2="value2")

        # simple strings
        l = Location('host.com.br:1000/Class/name?option1=value1,option2=value2')
        assert l

        assert l.host == 'host.com.br'
        assert l.port == 1000
        assert l.cls == "Class"
        assert l.name == "name"
        assert l.config == dict(option1="value1", option2="value2")

        # from dict
        assert_raises(InvalidLocationException, Location, cls="Class", config=dict(option1="value1", option2="value2"))
        assert_raises(InvalidLocationException, Location, name="name", config=dict(option1="value1", option2="value2"))
        assert_raises(InvalidLocationException, Location, config=dict(option1="value1", option2="value2"))
        assert_raises(InvalidLocationException, Location, cls="Class", name="")
        assert_raises(InvalidLocationException, Location, cls="", name="name")
        assert_raises(InvalidLocationException, Location, cls="", name="")
        
        assert Location(cls="Class", name="0")

        # simple version
        l = Location(cls="Class", name="name", config=dict(option1="value1", option2="value2"))
        assert l
        
        assert l.cls == "Class"
        assert l.name == "name"
        assert l.config == dict(option1="value1", option2="value2")
        assert type(str(l)) == StringType        

        # host version
        l = Location(host='host.com.br', port=1000, cls="Class", name="name", config=dict(option1="value1", option2="value2"))
        assert l
        assert l.host == 'host.com.br'
        assert l.port == 1000
        assert l.cls == "Class"
        assert l.name == "name"
        assert l.config == dict(option1="value1", option2="value2")
        assert type(str(l)) == StringType

        l = Location(host='host.com.br', cls="Class", name="name", config=dict(option1="value1", option2="value2"))
        assert l
        assert l.host == 'host.com.br'
        assert l.port == None
        assert l.cls == "Class"
        assert l.name == "name"
        assert l.config == dict(option1="value1", option2="value2")
        assert type(str(l)) == StringType

        assert_raises(InvalidLocationException, Location, host='host.com.br', port="xyz",
                                                          cls="Class", name="name",
                                                          config=dict(option1="value1", option2="value2"))

        # copy constructor
        l1 = Location('/Class/name')
        l2 = Location(l1)

        assert l1
        assert l2
        
        assert l2.cls == l1.cls
        assert l2.name == l1.name
        assert l2.config == l1.config

        assert l2 == l1
        assert id(l2) != id(l1)


    def test_eq (self):

        l1 = Location('host.com.br:1000/Class/name?option1=value1,option2=value2')
        l2 = Location('othr.com.br:1001/Class/name?option3=value3,option4=value4')

        # equality tests apply only to class and name config doesn't matter
        assert hash(l1) == hash(l2)
        assert l1 == l2

        l3 = Location('host.com.br:1000/Class/name?option1=value1,option2=value2')
        l4 = Location('host.com.br:1000/Class/othr?option1=value1,option2=value2')

        # equality tests apply only to class and name config doesn't matter
        assert l3 != l4

    def test_valid (self):

        valid = ["/Class/other?option1=value1,option2=value2",
                 "/Class/other?",
                 "/class/o?option=",
                 "/Class/1??option=1",
                 "/12345Class/o",
                 "host.com.br:1000/Class/name",
                 "host.com.br/Class/name",
                 '200.100.100.100:1000/Class/name',
                 '200.100.100.100/Class/name',                 
                 Location("/Class/name"), # copy constructor
                 ]

        for l in valid:
            loc = Location (l)
            assert loc, "'%s' is not valid" % l

    def test_invalid (self):

        invalid = ["  /  Class   /   other   ?   option  1 = value1 , option2  =  value2", # spaces matter.
                   "/Who/am/I",
                   ":1000/Class/name", # port only valid with a host
                   ]

        for l in invalid:
            assert_raises (InvalidLocationException, Location, l)
