
from chimera.core.resources import ResourcesManager
from chimera.core.exceptions import InvalidLocationException, ObjectNotFoundException

from nose.tools import assert_raises

from types import StringType


class TestResources:

    def __init__ (self):
        # each test will receive a fresh new class, so define our fixture right here
        self.res = ResourcesManager ()

    def test_add (self):

        assert len (self.res) == 0

        assert self.res.add ("/Location/l1", "instance-1", "uri-1") == 0

        # location already added
        assert_raises(InvalidLocationException, self.res.add, "/Location/l1", "instance-1", "uri-1")
        
        assert self.res.add ("/Location/l2", "instance-2", "uri-2") == 1
        
        assert_raises(InvalidLocationException, self.res.add, "wrong location", "instance-2", "uri-2")

        assert "/Location/l1" in self.res
        assert "/Location/l2" in self.res
        assert "/Location/0" in self.res
        assert not "/LocationNotExistent/l2" in self.res

        assert len (self.res) == 2

    def test_str (self):

        assert len (self.res) == 0
        assert self.res.add ("/Location/l1", "instance-1", "uri-1") == 0
        assert type(str(self.res.get('/Location/0'))) == StringType
        

    def test_remove (self):

        assert len (self.res) == 0

        assert self.res.add ("/Location/l1", "instance-1", "uri-1") == 0
        assert self.res.remove ("/Location/l1") == True

        assert_raises(ObjectNotFoundException, self.res.remove, "/What/l1")
        assert_raises(InvalidLocationException, self.res.remove, "wrong location")

        assert "/Location/l1" not in self.res

    def test_get (self):

        assert len (self.res) == 0


        assert self.res.add ("/Location/l2", "instance-2", "uri-2") == 0
        assert self.res.add ("/Location/l1", "instance-1", "uri-1") == 1

        ret = self.res.get ("/Location/l1")

        assert ret.location == "/Location/l1"
        assert ret.instance == "instance-1"
        assert ret.uri == "uri-1"

        assert_raises(ObjectNotFoundException, self.res.get, "/Location/l99")

        # get using subscription
        assert self.res["/Location/l1"].location == "/Location/l1"
        assert_raises(KeyError, self.res.__getitem__, "/LocationNotExistent/l1")
        assert_raises(KeyError, self.res.__getitem__, "wrong location")        
        

        # get by index
        assert self.res.get("/Location/0").location == "/Location/l2"
        assert self.res.get("/Location/1").location == "/Location/l1"
        assert_raises(ObjectNotFoundException, self.res.get, '/Location/9')
        assert_raises(ObjectNotFoundException, self.res.get, '/LocationNotExistent/0')        
        assert_raises(InvalidLocationException, self.res.get, 'wrong location')



    def test_get_by_class (self):
        
        assert len (self.res) == 0
        
        assert self.res.add ("/Location/l1", "instance-1", "uri-1") == 0
        assert self.res.add ("/Location/l2", "instance-2", "uri-2") == 1

        entries = [self.res.get ("/Location/l1"), self.res.get ("/Location/l2")]

        # get by class
        found = self.res.getByClass ("Location")
        
        assert (entries == found)

