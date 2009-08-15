#!/usr/bin/env python
# -*- coding: utf-8 -*-

from chimera.core.chimeraobject import ChimeraObject
from chimera.core.constants import SYSTEM_CONFIG_DIRECTORY

import cherrypy
import simplejson

import threading
import os

class WebAdminRoot (object):

    def __init__ (self, controller):
        self.controller = controller
        
    @cherrypy.expose
    def index (self):
        return open(os.path.join(os.path.dirname(__file__), "webadmin.html")).read()

    @cherrypy.expose
    def is_dome_open (self):
        response = cherrypy.response
        response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(self.controller.dome.isSlitOpen())

    @cherrypy.expose
    def open_dome (self):

        try:
            self.controller.dome.openSlit()
        except Exception:
            return "Erro ao tentar abrir a cúpula!"

        return "Sucesso!"

    @cherrypy.expose
    def close_dome (self):

        try:
            self.controller.dome.closeSlit()
        except Exception:
            return "Erro ao tentar fechar a cúpula!"

        return "Sucesso!"
    
class WebAdmin (ChimeraObject):

    __config__ = {"dome": "/Dome/0"}
    
    def __init__ (self):
        ChimeraObject.__init__(self)

    def __start__ (self):

        try: 
            self.dome = self.getManager().getProxy(self["dome"])
        except Exception:
            self.log.warning("No dome available, Web Admin would be disabled.")
            return False

        cherrypy.config.update({"engine.autoreload_on": False,
                                "server.socket_host": self.getManager().getHostname(),
                                "server.socket_port": 8080,
                                "log.screen": False,
                                "log.error_file": os.path.join(SYSTEM_CONFIG_DIRECTORY, "webadmin_error.log"),
                                "log.access_file": os.path.join(SYSTEM_CONFIG_DIRECTORY, "webadmin_access.log")})                                

        current_dir = os.path.dirname(os.path.abspath(__file__))
                                      
        app_config = {"/": {},
                      "/jquery-1.3.2.js": {"tools.staticfile.on": True,
                                           "tools.staticfile.filename": os.path.join(current_dir, "jquery-1.3.2.js")}                      
                      }

        def start():
            cherrypy.quickstart(WebAdminRoot(self), "/", app_config)
        
        threading.Thread(target=start).start()
        
        return True

    def __stop__ (self):
        cherrypy.engine.exit()
