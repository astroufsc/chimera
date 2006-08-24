
class Catalog:
    def __init__(self):
        pass
    
class Object:

    def __init__(self, name = "", ra = None, dec = None):

        self.name = name

        self.ra = ra
        self.dec = dec
        
        self.altitude = None
        self.azimuth = None

        self.ephoch = None

        self.resolvers = {}
