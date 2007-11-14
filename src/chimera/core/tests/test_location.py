
from chimera.core.location import Location

class TestLocation (object):

    def test_create (self):

        # simple strings
        l = Location('/Class/name?option1=value1,option2=value2')

        assert l.isValid()
        assert l.cls == "Class"
        assert l.name == "name"
        assert l.config == dict(option1="value1", option2="value2")

        # from dict
        l = Location(cls="Class", config=dict(option1="value1", option2="value2"))
        assert not l.isValid()

        l = Location(name="name", config=dict(option1="value1", option2="value2"))
        assert not l.isValid()
        
        l = Location(config=dict(option1="value1", option2="value2"))
        assert not l.isValid()

        l = Location(cls="Class", name="")
        assert not l.isValid()
        
        l = Location(cls="", name="name")
        assert not l.isValid()
        
        l = Location(cls="", name="")
        assert not l.isValid()

        l = Location(cls="Class", name="name", config=dict(option1="value1", option2="value2"))
        assert l.isValid()
        
        assert l.cls == "Class"
        assert l.name == "name"
        assert l.config == dict(option1="value1", option2="value2")

        # copy constructor
        l1 = Location('/Class/name')
        l2 = Location(l1)

        assert l1.isValid()
        assert l2.isValid()
        
        assert l2.cls == l1.cls
        assert l2.name == l1.name
        assert l2.config == l1.config

        assert l2 == l1
        assert id(l2) != id(l1)

        l1 = Location(' / C l a s s')
        l2 = Location(l1)

        assert not l1.isValid()
        assert not l2.isValid()
        

    def test_eq (self):

        l1 = Location('/Class/name?option1=value1,option2=value2')
        l2 = Location('/Class/name?option3=value3,option4=value4')

        # equality tests apply only to class and name config doesn't matter
        assert hash(l1) == hash(l2)
        assert l1 == l2

        l3 = Location('/Class/other?option1=value1,option2=value2')
        l4 = Location('/Class/rehto?option1=value1,option2=value2')

        # equality tests apply only to class and name config doesn't matter
        assert l3 != l4

    def test_valid (self):

        valid = ["/Class/other?option1=value1,option2=value2",
                 "/Class/other?",
                 "/class/o?option=",
                 "/Class/1??option=1",
                 "/12345Class/o",
                 Location("/Class/name"), # copy constructor
                 ]

        for l in valid:
            loc = Location (l)
            assert loc.isValid(), "'%s' is not valid" % l

    def test_invalid (self):

        invalid = ["  /  Class   /   other   ?   option  1 = value1 , option2  =  value2", # spaces matter.
                   Location("badLocation"), # copy constructor with invalid location
                   "/Who/am/I"
                   ]

        for l in invalid:
            loc = Location (l)
            assert not loc.isValid(), "'%s' is valid!" % l


