

from chimera.core.chimeraobject import ChimeraObject
from chimera.controllers.imageserver.imageserverhttp import ImageServerHTTP

from chimera.util.image import Image

import Pyro.util

import os


class ImageServer(ChimeraObject):

    __config__  = { # root directory where images are stored
                   'images_dir': '$HOME/images',    
                   # path relative to images_dir where images for a
                   # night will be stored, use "" to save all images
                   # on the same directory
                   'night_dir' : '$LAST_NOON_DATE', 

                   # Load existing images on startup?
                   'autoload': False,

                   'httpd': True, 
                   'http_host': 'default',
                   'http_port': 7669}
    
    def __init__(self):
        ChimeraObject.__init__(self)
        
        self.imagesByID   = {}
        self.imagesByPath = {}

    def __start__ (self):

        if self["http_host"] == "default":
            self["http_host"] = self.getManager().getHostname()
        
        if self["httpd"]:    
            self.http = ImageServerHTTP(self)
            self.http.start()
        
        if self['autoload']:
            self.log.info('Loading existing images...')
            loaddir = os.path.expanduser(self['images_dir'])
            loaddir = os.path.expandvars(loaddir)
            loaddir = os.path.realpath(loaddir)
            self._loadImageDir(loaddir)

    def __stop__(self):

        if self["httpd"]:    
            self.http.stop()

        for image in self.imagesByID.values():
            self.unregister(image)

    def _loadImageDir(self, dir):

        filesToLoad = []

        if os.path.exists(dir):        

            # build files list
            for root, dirs, files in os.walk(dir):
                filesToLoad += [os.path.join(dir, root, f) for f in files if f.endswith(".fits")]
                
            for file in filesToLoad:
                self.log.debug('Loading %s' % file)
                self.register(Image.fromFile(file))

    def register(self, image):
        try:
            if "CHM_ID" in image:
                image.setGUID(image["CHM_ID"])
            else:
                image += ("CHM_ID", image.GUID())
                image.save()
                
            self.getDaemon().connect(image)
            self.imagesByID[image.GUID()]    = image
            self.imagesByPath[image.filename()] = image

            # save Image's HTTP address
            image.http(self.getHTTPByID(image.GUID()))
            return image.getProxy()
        except Exception, e:
            print ''.join(Pyro.util.getPyroTraceback(e))

    def unregister(self, image):
        try:
            self.getDaemon().disconnect(image)
            del self.imagesByID[image.GUID()]
            del self.imagesByPath[image.filename()]
        except Exception, e:
            print ''.join(Pyro.util.getPyroTraceback(e))
    
    def getImageByID (self, id):
        if id in self.imagesByID:
            return self.imagesByID[id]

    def getImageByPath (self, path):
        if path in self.imagesByPath:
            return self.imagesByPath[path]

    def getProxyByID (self, id):
        img = self.getImageByID(id)
        if img:
            return img.getProxy()

    def getHTTPByID (self, id):
        return "http://%s:%d/image/%s" % (self["http_host"], int(self["http_port"]), str(id))

    def defaultNightDir(self):
        return os.path.join(self["images_dir"], self["night_dir"])
        
