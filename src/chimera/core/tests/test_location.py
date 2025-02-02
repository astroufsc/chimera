import pytest

from chimera.core.location import Location
from chimera.core.exceptions import InvalidLocationException


class TestLocation(object):

    def test_create(self):

        # simple strings
        loc = Location("/Class/name?option1=value1,option2=value2")
        assert loc

        assert loc.host is None
        assert loc.port is None
        assert loc.cls == "Class"
        assert loc.name == "name"
        assert loc.config == dict(option1="value1", option2="value2")

        # simple strings
        loc = Location("host.com.br:1000/Class/name?option1=value1,option2=value2")
        assert loc

        assert loc.host == "host.com.br"
        assert loc.port == 1000
        assert loc.cls == "Class"
        assert loc.name == "name"
        assert loc.config == dict(option1="value1", option2="value2")

        # from dict
        with pytest.raises(InvalidLocationException):
            Location(cls="Class", config=dict(option1="value1", option2="value2"))
        with pytest.raises(InvalidLocationException):
            Location(name="name", config=dict(option1="value1", option2="value2"))
        with pytest.raises(InvalidLocationException):
            Location(config=dict(option1="value1", option2="value2"))
        with pytest.raises(InvalidLocationException):
            Location(cls="Class", name="")
        with pytest.raises(InvalidLocationException):
            Location(cls="", name="name")
        with pytest.raises(InvalidLocationException):
            Location(cls="", name="")

        assert Location(cls="Class", name="0")

        # simple version
        loc = Location(
            cls="Class", name="name", config=dict(option1="value1", option2="value2")
        )
        assert loc

        assert loc.cls == "Class"
        assert loc.name == "name"
        assert loc.config == dict(option1="value1", option2="value2")

        # host version
        loc = Location(
            host="host.com.br",
            port=1000,
            cls="Class",
            name="name",
            config=dict(option1="value1", option2="value2"),
        )
        assert loc
        assert loc.host == "host.com.br"
        assert loc.port == 1000
        assert loc.cls == "Class"
        assert loc.name == "name"
        assert loc.config == dict(option1="value1", option2="value2")

        loc = Location(
            host="host.com.br",
            cls="Class",
            name="name",
            config=dict(option1="value1", option2="value2"),
        )
        assert loc
        assert loc.host == "host.com.br"
        assert loc.port is None
        assert loc.cls == "Class"
        assert loc.name == "name"
        assert loc.config == dict(option1="value1", option2="value2")

        with pytest.raises(InvalidLocationException):
            Location(
                host="host.com.br",
                port="xyz",
                cls="Class",
                name="name",
                config=dict(option1="value1", option2="value2"),
            )

        # copy constructor
        l1 = Location("/Class/name")
        l2 = Location(l1)

        assert l1
        assert l2

        assert l2.cls == l1.cls
        assert l2.name == l1.name
        assert l2.config == l1.config

        assert l2 == l1
        assert id(l2) != id(l1)

    def test_eq(self):

        l1 = Location("host.com.br:1000/Class/name?option1=value1,option2=value2")
        l2 = Location("othr.com.br:1001/Class/name?option3=value3,option4=value4")

        # equality tests apply only to class and name config doesn't matter
        assert hash(l1) == hash(l2)
        assert l1 == l2

        l3 = Location("host.com.br:1000/Class/name?option1=value1,option2=value2")
        l4 = Location("host.com.br:1000/Class/othr?option1=value1,option2=value2")

        # equality tests apply only to class and name config doesn't matter
        assert l3 != l4

    def test_valid(self):

        valid = [
            "/Class/other?option1=value1,option2=value2",
            "/Class/other?",
            "/class/o?option=",
            "/Class/1??option=1",
            "/12345Class/o",
            "host.com.br:1000/Class/name",
            "host.com.br/Class/name",
            "200.100.100.100:1000/Class/name",
            "200.100.100.100/Class/name",
            Location("/Class/name"),  # copy constructor
        ]

        for loc in valid:
            loc = Location(loc)
            assert loc, f"'{loc}' is not valid"

    def test_invalid(self):

        invalid = [
            "  /  Class   /   other   ?   option  1 = value1 , option2  =  value2",  # spaces matter.
            "/Who/am/I",
            ":1000/Class/name",  # port only valid with a host
        ]

        for loc in invalid:
            with pytest.raises(InvalidLocationException):
                Location(loc)
