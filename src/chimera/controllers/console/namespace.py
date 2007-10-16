

class Namespace (list):

    def __init__ (self):
        list.__init__ (self)

    def __contains__ (self, name):

        for cmd in self:
            if cmd.name () == name or name in cmd.aliases():
                return True

        return False

    def names (self):
        names = [cmd.name() for cmd in self]

        for cmd in self:
            names += cmd.aliases()

        return names    
