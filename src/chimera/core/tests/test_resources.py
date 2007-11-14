
from chimera.core.resources import ResourcesManager

class TestResources:

    def __init__ (self):
        # each test will receive a fresh new class, so define our fixture right here
        self.res = ResourcesManager ()

    def test_add (self):

        assert len (self.res) == 0

        assert self.res.add ("/Location/l1", "instance-1", "uri-1") == 0
        assert self.res.add ("/Location/l2", "instance-2", "uri-2") == 1

        assert "/Location/l1" in self.res
        assert "/Location/l2" in self.res

        assert len (self.res) == 2

    def test_remove (self):

        assert len (self.res) == 0

        assert self.res.add ("/Location/l1", "instance-1", "uri-1") == 0
        assert self.res.remove ("/Location/l1") == True

        assert "/Location/l1" not in self.res

    def test_get (self):

        assert len (self.res) == 0


        assert self.res.add ("/Location/l2", "instance-2", "uri-2") == 0
        assert self.res.add ("/Location/l1", "instance-1", "uri-1") == 1

        ret = self.res.get ("/Location/l1")

        assert ret.location == "/Location/l1"
        assert ret.instance == "instance-1"
        assert ret.uri == "uri-1"

        assert not self.res.get ("/Location/l99")

        # get using subscription
        assert self.res["/Location/l1"].location == "/Location/l1"

        # get by index
        assert self.res.get("/Location/0").location == "/Location/l2"
        assert self.res.get("/Location/1").location == "/Location/l1"        


    def test_get_by_class (self):
        
        assert len (self.res) == 0
        
        assert self.res.add ("/Location/l1", "instance-1", "uri-1") == 0
        assert self.res.add ("/Location/l2", "instance-2", "uri-2") == 1

        entries = [self.res.get ("/Location/l1"), self.res.get ("/Location/l2")]

        # get by class
        found = self.res.getByClass ("Location")
        
        assert (entries == found)

