
import cherrypy
from cherrypy.lib.static import serve_file

import threading
import logging

class ImageServerHTTP(threading.Thread):

    def __init__ (self, ctrl):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("Image Server HTTPD")
        self.ctrl = ctrl

        # less verbose cherry
        logging.getLogger("cherrypy.error").setLevel(logging.WARNING)

        cherrypy.config.update({"server.socket_port": self.ctrl['http_port'],
                                "server.socket_host": self.ctrl['http_host'],
                                "tools.encode.on": True,
                                "tools.encode.encoding": "iso-8859-1",
                                "tools.decode.on": True,
                                "tools.trailing_slash.on": True,
                                "engine.autoreload_on": False})
    def run(self):
        cherrypy.quickstart(self)

    def stop(self):
        cherrypy.engine.stop()
        self.join()
                
    @cherrypy.expose
    def index (self, *args, **kwargs):
        return "All your images belong to us."

    @cherrypy.expose
    def image (self, *args, **kwargs):
        if args:

            img = self.ctrl.getImageByID(args[0])

            if not img:
                return "Couldn't find the image."
            return serve_file(img.filename(), "image/fits", "attachment")

        else:
            return "What are you looking for?"

    @cherrypy.expose
    def list(self, *args, **kwargs):
        toReturn = '<table><tr><th>Image ID</th><th>Path</th></tr>'
        keys = self.ctrl.imagesByPath.keys()
        keys.sort()
        for key in keys:
            image = self.ctrl.imagesByPath[key]
            id = image.GUID()
            path = image.filename()
            toReturn += ('<tr><td><a href="/image/%s">%s</a></td><td><a href="/image/%s">%s</a></td></tr>' %
                         (id,id,id,path))
        return toReturn
