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
    def start (self):

        try:
            self.controller.dome.openSlit()
            self.controller.telescope.unpark()
            # clean scheduler database
            self.controller.scheduler.restartAllPrograms()
            self.controller.scheduler.start()
        except Exception:
            return "Erro ao tentar iniciar o sistema!"

        return "Sucesso!"

    @cherrypy.expose
    def stop (self):

        try:
            self.controller.scheduler.stop()
            self.controller.telescope.park()
            self.controller.dome.closeSlit()
        except Exception:
            return "Erro ao tentar parar o sistema!"

        return "Sucesso!"

    @cherrypy.expose
    def pause (self):
        try:
            self.controller.dome.openSlit()
            self.controller.telescope.unpark()
            self.controller.scheduler.start()
        except Exception:
            return "Erro ao tentar continuar os trabalhos!"

        return "Sucesso!"

    
class WebAdmin (ChimeraObject):

    __config__ = {"dome": "/Dome/0",
                  "scheduler": "/Scheduler/0",
                  "telescope": "/Telescope/0",
                  "host": "default",
                  "port": 8080}
    
    def __init__ (self):
        ChimeraObject.__init__(self)

    def __start__ (self):

        try: 
            self.dome = self.getManager().getProxy(self["dome"])
            self.scheduler = self.getManager().getProxy(self["scheduler"])
            self.telescope = self.getManager().getProxy(self["telescope"])
        except Exception:
            self.log.warning("No dome, scheduler or telescope available, Web Admin would be disabled.")
            return False

        if self["host"] == "default":
            self["host"] = self.getManager().getHostname()

        cherrypy.config.update({"engine.autoreload_on": False,
                                "server.socket_host": self["host"],
                                "server.socket_port": self["port"],
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
