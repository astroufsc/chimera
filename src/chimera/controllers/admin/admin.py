from cherrypy import expose

import cherrypy

class Admin (object):

    def __init__ (self):
        self.acao = Acao ()

    @expose
    def index (self, *args, **kwargs):
        return ""

class Acao (object):
    
    @expose
    def index (self, *args, **kwargs):
        print args
        print kwargs
        return "Olah Mundo"
    

if __name__ == "__main__":

    cherrypy.quickstart (Admin())
