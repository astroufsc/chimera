from chimera.core.chimeraobject import ChimeraObject
from chimera.controllers.imageserver.imageserverhttp import ImageServerHTTP

from chimera.util.image import Image

import os

from collections import OrderedDict


class ImageServer(ChimeraObject):

    __config__ = {  # root directory where images are stored
        "images_dir": "~/images",
        # path relative to images_dir where images for a
        # night will be stored, use "" to save all images
        # on the same directory
        "night_dir": "$LAST_NOON_DATE",
        # Load existing images on startup?
        "autoload": False,
        "httpd": True,
        "http_host": "default",
        "http_port": 7669,
        "max_images": 10,
    }

    def __init__(self):
        ChimeraObject.__init__(self)

        self.imagesByID = OrderedDict()
        self.imagesByPath = OrderedDict()

    def __start__(self):

        if self["http_host"] == "default":
            self["http_host"] = self.getManager().getHostname()

        if self["httpd"]:
            self.http = ImageServerHTTP(self)
            self.http.start()

        if self["autoload"]:
            self.log.info("Loading existing images...")
            loaddir = os.path.expanduser(self["images_dir"])
            loaddir = os.path.expandvars(loaddir)
            loaddir = os.path.realpath(loaddir)
            self._loadImageDir(loaddir)

    def __stop__(self):

        if self["httpd"]:
            self.http.stop()

        for image in list(self.imagesByID.values()):
            self.unregister(image)

    def _loadImageDir(self, dir):

        filesToLoad = []

        if os.path.exists(dir):

            # build files list
            for root, dirs, files in os.walk(dir):
                filesToLoad += [
                    os.path.join(dir, root, f) for f in files if f.endswith(".fits")
                ]

            for file in filesToLoad:
                self.log.debug(f"Loading {file}")
                self.register(Image.fromFile(file))

    def register(self, image):
        if len(self.imagesByID) > self["max_images"]:
            remove_items = list(self.imagesByID.keys())[: -self["max_images"]]

            for item in remove_items:
                self.log.debug(f"Unregistering image {item}")
                self.unregister(self.imagesByID[item])

        self.imagesByID[image.id] = image
        self.imagesByPath[image.filename] = image

        # save Image's HTTP address
        image.http(self.getHTTPByID(image.id))

        return image

    def unregister(self, image):
        del self.imagesByID[image.id]
        del self.imagesByPath[image.filename]

    def getImageByID(self, id):
        if id in self.imagesByID:
            return self.imagesByID[id]

    def getImageByPath(self, path):
        if path in self.imagesByPath:
            return self.imagesByPath[path]

    def getProxyByID(self, id):
        img = self.getImageByID(id)
        if img:
            return img.getProxy()

    def getHTTPByID(self, id):
        return f"http://{self['http_host']}:{int(self['http_port'])}/image/{id}"

    def defaultNightDir(self):
        return os.path.join(self["images_dir"], self["night_dir"])
