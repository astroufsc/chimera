import os
from collections import OrderedDict

from chimera.controllers.imageserver.imageserverhttp import ImageServerHTTP
from chimera.core.chimeraobject import ChimeraObject
from chimera.util.image import Image


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

        self.images_by_id = OrderedDict()
        self.images_by_path = OrderedDict()

    def __start__(self):
        if self["http_host"] == "default":
            self["http_host"] = self.__bus__.url.host

        if self["httpd"]:
            self.http = ImageServerHTTP(self)
            self.http.start()

        if self["autoload"]:
            self.log.info("Loading existing images...")
            load_dir = os.path.expanduser(self["images_dir"])
            load_dir = os.path.expandvars(load_dir)
            load_dir = os.path.realpath(load_dir)
            self._load_image_dir(load_dir)

    def __stop__(self):
        if self["httpd"]:
            self.http.stop()

        for image in list(self.images_by_id.values()):
            self.unregister(image)

    def _load_image_dir(self, dir):
        files_to_load = []

        if os.path.exists(dir):
            # build files list
            for root, dirs, files in os.walk(dir):
                files_to_load += [
                    os.path.join(dir, root, f) for f in files if f.endswith(".fits")
                ]

            for file in files_to_load:
                self.log.debug(f"Loading {file}")
                self.register(Image.from_file(file))

    def register(self, image_filename):
        if len(self.images_by_id) > self["max_images"]:
            remove_items = list(self.images_by_id.keys())[: -self["max_images"]]

            for item in remove_items:
                self.log.debug(f"Unregistering image {item}")
                self.unregister(self.images_by_id[item])

        image = Image.from_file(image_filename, mode="readonly")
        self.images_by_id[image.id] = image
        self.images_by_path[image.filename] = image

        # save Image's HTTP address
        image.http(self.get_http_by_id(image.id))

        return image.http()

    def unregister(self, image):
        del self.images_by_id[image.id]
        del self.images_by_path[image.filename]

    def get_image_by_id(self, id):
        if id in self.images_by_id:
            return self.images_by_id[id]

    def get_image_by_path(self, path):
        if path in self.images_by_path:
            return self.images_by_path[path]

    def get_proxy_by_id(self, id):
        img = self.get_image_by_id(id)
        if img:
            return img.get_proxy()

    def get_http_by_id(self, id):
        return f"http://{self['http_host']}:{int(self['http_port'])}/image/{id}"

    def default_night_dir(self):
        return os.path.join(self["images_dir"], self["night_dir"])
