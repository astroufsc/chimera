import readline

from chimera.core.lifecycle import BasicLifeCycle

class MeadeDebug (BasicLifeCycle):


    __options__ = {"script": "meade.script.default"}

    def __init__ (self, manager):
        BasicLifeCycle.__init__(self, manager)

    def init (self, config):

        self.config += config

        return True

    def main (self):

        m = self.manager.getDriver ('/Meade/lx16?device=/dev/ttyS1')

        if self.config.script != "meade.script.default":

            try:
                f = open (self.config.script)

                for line in f:
                    if not line:
                        continue
                    
                    m._write (':%s#' % line[:-1])

                    print m._readline ()

                f.close ()
            except IOError, e:
                print "Error: %s (%s)" % (e.strerror, e.filename)
        else:

            print "Meade protocol debugger"

            try:

                while True:
                    i = raw_input ( "> ")

                    if not i:
                        continue

                    m._write (":%s#" % i)
                    o = m._readline ()

                    print o

            except EOFError:
                print "Bye!"
        
                
    

