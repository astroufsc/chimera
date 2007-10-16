from chimera.util.output import red, blue, bold, faint

class Message (object):

    def __init__ (self, msg = None):
        self.msg = msg or ""

    def __str__ (self):
        return str(self.msg)

class Error (Message):

    def __init__ (self, msg):
        Message.__init__ (self, msg)

    def __str__ (self):
        return red (str(self.msg))
    
class Hint (Message):

    def __init__ (self, msg):
        Message.__init__ (self, msg)

    def __str__ (self):
        return blue (str(self.msg))
    

class Config (Message):

    def __init__ (self, msg):
        Message.__init__ (self, msg)

        self.msg = msg
        self._str = ""

        max_keys = max ( [ len(k) for k in msg ])

        names = msg.keys()
        names.sort()

        for k in names:
            self._str += "%s : %s (%s)\n" % (bold(k.ljust(max_keys+3)), str(msg[k]), faint(type(msg[k]).__name__))

        self._str = self._str[:-1]

    def __str__ (self):
        return self._str
    
