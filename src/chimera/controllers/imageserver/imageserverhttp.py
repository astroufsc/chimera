
import threading
import logging
import os

from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer   import HTTPServer

class ImageServerHTTPHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path.startswith("/image/"):
            self.image()
        else:
            self.list()

    def log_message(self, format, *args):
        self.server.ctrl.log.info("%s - - [%s] %s" %
                                  (self.address_string(),
                                   self.log_date_time_string(),
                                   format%args))

    def send_head(self, response=200, ctype=None, length=None, modified=None):
        self.send_response(response)
        self.send_header("Content-type", ctype or "text/plain")
        self.send_header("Content-Length", length or 1)
        self.send_header("Last-Modified", self.date_time_string(modified))
        self.end_headers()

    def response(self, code, txt, ctype):
        self.send_head(code, ctype, len(txt))
        self.wfile.write(txt)

    def response_file(self, filename, ctype):
        f = open(filename)
        if not f:
            self.response(404, "Couldn't find")
        else:
            fs = os.fstat(f.fileno())
            self.send_head(200, "image/fits",  str(fs[6]), fs.st_mtime)
            self.copyfile(f, self.wfile)
            f.close()

    def image (self):

        args = self.path.split("/image/")

        if len(args) < 2:
            return self.response(200, "What are you looking for?")
        else:
            img = self.server.ctrl.getImageByID(args[1])
            if not img:
                self.response(200, "Couldn't find the image.")
            else:
                self.response_file(img.filename(), "image/fits")

    def list(self):

        toReturn = '<table><tr><th>Image ID</th><th>Path</th></tr>'
        keys = self.server.ctrl.imagesByPath.keys()
        keys.sort()
        for key in keys:
            image = self.server.ctrl.imagesByPath[key]
            id = image.GUID()
            path = image.filename()
            toReturn += ('<tr><td><a href="/image/%s">%s</a></td><td><a href="/image/%s">%s</a></td></tr>' %
                         (id,id,id,path))

        self.response(200, toReturn, "text/html")

class ImageServerHTTP(threading.Thread):

    def __init__ (self, ctrl):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.setName("Image Server HTTPD")
        self.ctrl = ctrl
        self.die = threading.Event()

    def keep_running(self):
        return self._keep_running

    def run(self):

        srv = HTTPServer((self.ctrl['http_host'], self.ctrl['http_port']), ImageServerHTTPHandler)
        self.ctrl.log.info("Starting HTTP server on %s:%d" % (self.ctrl['http_host'], self.ctrl['http_port']))

        self.die.clear()

        srv.ctrl = self.ctrl
        srv.timeout = 1

        while not self.die.isSet():
            srv.handle_request()

    def stop(self):
        self.die.set()

