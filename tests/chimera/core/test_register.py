
from chimera.core.register import Register
from chimera.core.location import Location

class TestRegister:

    def setup_method (self, method):
        self.register = Register ()

        self.location_a = "/object/instancia1"
        self.location_b = "/object/instancia2"

        self.location_c = "/int/instancia1"
        self.location_d = "/int/instancia2"

        self.location_e = Location("/float/instancia1")
        self.location_f = Location("/float/instancia2")

        self.a = object ()
        self.b = object ()
        
        self.c = int (1)
        self.d = int (2)

        self.e = float (1.0)
        self.f = float (2.0)

    def test_register (self):

        # basic insert
        assert self.register.register (self.location_a, self.a) == True
        # insert already inserted shoud fail
        assert self.register.register (self.location_a, self.a) == False

        # contains a? OK
        assert (self.location_a in self.register) == True
        # contains f, not, please return False!
        assert (self.location_f in self.register) == False

    def test_unregister (self):

        assert self.register.register (self.location_a, self.a) == True
        assert self.register.unregister(self.location_a) == True

        # removed?
        assert (self.location_a in self.register) == False

    def test_get (self):

        assert self.register.register (self.location_a, self.a) == True
        assert self.register.register (self.location_b, self.b) == True

        # get method
        assert (self.register.get (self.location_a).location == self.location_a)
        assert (self.register.get (self.location_a).instance == self.a)        

        # get using subscription
        assert (self.register[self.location_a].location == self.location_a)
        assert (self.register[self.location_a].instance == self.a)

        # get by index
        assert self.register.get("/object/0").instance == self.a
        assert self.register.get("/object/1").instance == self.b
        assert self.register.get("/object/2") == False

    def test_get_by_class (self):
        
        assert self.register.register (self.location_a, self.a) == True
        assert self.register.register (self.location_b, self.b) == True

        entries = [self.register.get (self.location_a), self.register.get (self.location_b)]

        # get by class
        found = self.register.getByClass ("object")
        
        assert (entries == found)

