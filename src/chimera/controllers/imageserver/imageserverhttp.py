# import logging
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler


class ImageServerHTTPHandler(SimpleHTTPRequestHandler):

    def do_GET(self):  # noqa: N802
        if self.path.startswith("/image/"):
            self.image()
        else:
            self.list()

    def log_message(self, format, *args):
        self.server.ctrl.log.info(
            f"{self.address_string()} - - [{self.log_date_time_string()}] {format % args}"
        )

    def send_head(self, response=200, ctype=None, length=None, modified=None):
        self.send_response(response)
        self.send_header("Content-type", ctype or "text/plain")
        self.send_header("Content-Length", length or 1)
        self.send_header("Last-Modified", self.date_time_string(modified))
        self.end_headers()

    def response(self, code: int, txt: str, ctype: str):
        self.send_head(code, ctype, len(txt))
        self.wfile.write(txt.encode())

    def response_file(self, filename, ctype):
        f = open(filename, "rb")
        if not f:
            self.response(404, "Couldn't find")
        else:
            fs = os.fstat(f.fileno())
            self.send_head(200, "image/fits", str(fs[6]), fs.st_mtime)
            self.copyfile(f, self.wfile)
            f.close()

    def image(self):

        args = self.path.split("/image/")

        if len(args) < 2:
            return self.response(200, "What are you looking for?")
        else:
            img = self.server.ctrl.get_image_by(args[1])
            if not img:
                self.response(200, "Couldn't find the image.")
            else:
                self.response_file(img.filename, "image/fits")

    def list(self):

        to_return = "<table><tr><th>Image ID</th><th>Path</th></tr>"
        keys = list(self.server.ctrl.images_by_path.keys())
        keys.sort()
        for key in keys:
            image = self.server.ctrl.images_by_path[key]
            id = image.GUID()
            path = image.filename
            to_return += f'<tr><td><a href="/image/{id}">{id}</a></td><td><a href="/image/{id}">{path}</a></td></tr>'

        self.response(200, to_return, "text/html")


class ImageServerHTTP(threading.Thread):

    def __init__(self, ctrl):
        threading.Thread.__init__(self)
        self.daemon = True
        self.name = "Image Server HTTPD"
        self.ctrl = ctrl
        self.die = threading.Event()

    def run(self):

        srv = HTTPServer(
            (self.ctrl["http_host"], self.ctrl["http_port"]), ImageServerHTTPHandler
        )
        self.ctrl.log.info(
            f"Starting HTTP server on {self.ctrl['http_host']}:{self.ctrl['http_port']}"
        )

        self.die.clear()

        srv.ctrl = self.ctrl
        srv.timeout = 1

        while not self.die.is_set():
            srv.handle_request()

    def stop(self):
        self.die.set()
