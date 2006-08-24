from types import StringType

class Register(object):

    def __init__(self, kind = None):

        self.objects = {}

    def register(self, location, instance):

        if location in self.objects:
            return False

        self.objects[location] = instance

    def unregister(self, location):
        if not location in self.objects:
            return False

        del self.objects[location]

    def update(self, location, instance):
        self.unregister(location)
        self.register(location, instance)

    def __repr__(self):
        _str = "There are %d objects avaiable.\n" % len(self.objects)
        _str += self.objects.__repr__()
        
        return _str

    def __contains__(self, item):
        _ret = filter(lambda x: x == item, self.objects.keys())

        if _ret:
            return True
        else:
            return False

    def __len__(self):
        return self.objects.__len__()

    def __iter__(self):
        return self.objects.__iter__()

    def items(self):
        return self.objects.items()

    def keys(self):
        return self.objects.keys()

    def values(self):
        return self.objects.values()
    
    def __getitem__(self, item):
        r = self.get(item)

        if not r:
            raise KeyError
        else:
            return r

    def get(self, item):

        if type(item) == StringType:
            item = Location(item)
            
            if not item.isValid():
                return False

            # try to get by index first
            try:
                numberedInstance = True
                number = int(item._name)
            except ValueError:
                numberedInstance = False

            if numberedInstance:
                return self.getByIndex(item._class, number)

        if self.__contains__(item):
            ret = filter(lambda x: x == item, self.objects.keys())
            
            return self.objects[ret[0]]
        else:
            return False


    def getByClass(self, cls):

        _insts = filter(lambda inst: inst._class == cls, self.objects.keys())

        return _insts

    def getByIndex(self, cls, index):
        
        insts = self.getByClass(cls)

        if insts:
            try:
                ret = self.get(insts[index])
                return ret
            except IndexError:
                return False
        else:
            return False


if __name__ == '__main__':

    from uts.core.location import Location
    a = object()
    l = Location("/Telescope/meade?opt1=val1,opt2=val2")

    b = object()
    ll = Location("/Telescope/paramount?opt1=val1,opt2=val2")


    r = Register()
    r.register(l, a)
    r.register(ll, b)

    print r
    print r[l]
    print r["/Telescope/meade"]

    lll = r.getByClass("Telescope")
    for i in lll:
        print r[i]
