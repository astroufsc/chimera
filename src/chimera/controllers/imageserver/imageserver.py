from chimera.core.chimeraobject import ChimeraObject
from chimera.util.filenamesequence import FilenameSequence
from chimera.core.manager import Manager
from chimera.core.exceptions import ObjectNotFoundException, ClassLoaderException
from chimera.core.path import ChimeraPath
from chimera.controllers.imageserver.imageuri import ImageURI
from chimera.controllers.imageserver.image import Image
from chimera.core.site import Site
from chimera.controllers.imageserver.util import InvalidFitsImageException
import Pyro.util

import cherrypy
from cherrypy.lib.static import serve_file

import time
import datetime
import os
import os.path
import string
import random
import threading

dateFormat="%d%m%y"
timeFormat="%H%M%S"
noondateFormat="%Y-%m-%d"

class ImageServer(ChimeraObject):
    __config__  = {'savedir':   '$HOME/images/$NOONDATE',
                   
                   #Root directory where images are stored for use when autoloading existing
                   #for use when autoloading existing
                   'loaddir':   '$HOME/images',

                   #Load existing loaddir images on startup
                   'autoload':  True,
                   
                   'http_host': '0.0.0.0',
                   'http_port': 7669,
                   'site':      '/Site/0',
                   }
    
    def __init__(self):
        ChimeraObject.__init__(self)
        
        self.imagesByID = {}
        self.imagesByPath = {}
        self.mySite = None

    def __start__ (self):
        cherrypy.config.update({"server.socket_port": self['http_port'],
                                "server.socket_host":  self['http_host'],
                                "tools.encode.on": True,
                                "tools.encode.encoding": "iso-8859-1",
                                "tools.decode.on": True,
                                "tools.trailing_slash.on": True,
                                "engine.autoreload_on": False})

        class ImageServerHTTP(threading.Thread):

            def __init__ (self, ctrl):
                threading.Thread.__init__(self)
                self.setDaemon(True)
                self.ctrl = ctrl
            
            def run(self):
                cherrypy.quickstart(self)
                
            @cherrypy.expose
            def index (self, *args, **kwargs):
                return "All your images are belong to us."

            @cherrypy.expose
            def image (self, *args, **kwargs):
                if args:
                    uri = ImageURI(self.ctrl, args[0])

                    img = self.ctrl.getImageByURI(uri)

                    if not img:
                        return "Couldn't found the image."

                    return serve_file(img.getPath(), "image/fits", "attachment")


                else:
                    return "What are you looking for?"
            
            @cherrypy.expose
            def list(self, *args, **kwargs):
                toReturn = '<table><tr><th>Image ID</th><th>Path</th></tr>'
                keys = self.ctrl.imagesByPath.keys()
                keys.sort()
                for key in keys:
                    image = self.ctrl.imagesByPath[key]
                    id = image.getID()
                    path = image.getPath()
                    toReturn += ('<tr><td><a href="/image/%s">%s</a></td><td><a href="/image/%s">%s</a></td></tr>' %
                                 (id,id,id,path))
                return toReturn

        self.http = ImageServerHTTP(self)
        self.http.start()
        
        
        if self['autoload']:
            self.log.info('Loading existing images...')
            loaddir = os.path.expanduser(self['loaddir'])
            loaddir = os.path.expandvars(loaddir)
            loaddir = os.path.realpath(loaddir)
            self.__loadImageDir(loaddir)
    
    def __loadImageDir(self, dir):
        if os.path.exists(dir):
            files = os.listdir(dir)
            for file in files:
                file = os.path.join(dir, file)
                if os.path.isdir(file):
                    self.__loadImageDir(file)
                elif os.path.isfile(file):
                    if file.endswith('.fits'):
                        self.log.debug('Loading %s' % file)
                        try:
                            self.registerImage(Image(file, register=False))
                        except InvalidFitsImageException, e:
                            self.log.warning(str(e))

    def getFileName(self, filename='$DATE-$TIME'):
        try:
            now = time.gmtime()
            timeNow = self.getSiteProxy().localtime()
            if timeNow.hour < 12:
                timeNow = time.localtime(time.time() - 86400)  #subtract 1 day
            else:
                timeNow = time.localtime()

            subs_dict = {"DATE"     : time.strftime(dateFormat, now),
                         "TIME"     : time.strftime(timeFormat, now),
                         "NOONDATE" : time.strftime(noondateFormat, timeNow)}

            dest = string.Template(self['savedir']).safe_substitute(subs_dict)
            dest = os.path.expanduser(dest)
            dest = os.path.expandvars(dest)
            dest = os.path.realpath(dest)
            
            if not os.path.exists(dest):
                os.makedirs(dest)
            if not os.path.isdir(dest):
                raise OSError('A file with the same name as the desired dir already exists.')
            
            filename = string.Template(filename).safe_substitute(subs_dict)
            
            seq_num = FilenameSequence(os.path.join(dest, filename), extension='fits').next()
    
            finalname = os.path.join(dest, "%s-%04d%s%s" % (filename, seq_num, os.path.extsep, 'fits'))
            
            if os.path.exists(finalname):
                tmp = finalname
                finalname = os.path.join(dest, "%s-%04d%s%s" % (filename, int (random.random()*1000),
                                                                os.path.extsep, 'fits'))
    
                self.log.debug ("Image %s already exists. Saving to %s instead." %  (tmp, finalname))
            
            return finalname
        except Exception, e:
            print ''.join(Pyro.util.getPyroTraceback(e))
    
    def registerImage(self, image):
        try:
            self.getDaemon().connect(image)
            self.imagesByID[image.getID()] = image
            self.imagesByPath[image.getPath()] = image
        except Exception, e:
            print ''.join(Pyro.util.getPyroTraceback(e))
    
    def _isMyImage(self, imageURI):
        myMan = self.getManager()
        return ((imageURI.host == myMan.getHostname()) and (imageURI.port == myMan.getPort()))
    
    def getImageByURI(self, imageURI):
        if self._isMyImage(imageURI):
            return self.imagesByID[imageURI.config['hash']]
    
    def getProxyByURI(self, imageURI):
        if self._isMyImage(imageURI):
            return self.imagesByID[imageURI.config['hash']].getProxy()
    
    def getImageByPath(self, path):
        if path in self.imagesByPath.keys():
            return self.imagesByPath[path]
        else:
            return None
    
    def getSiteProxy(self):
        try:
            return self.getManager().getProxy(self['site'])
        except ObjectNotFoundException:
            if not self.mySite:
                self.mySite = Site()
            return self.mySite            
        
    def __stop__(self):
        cherrypy.engine.exit()
        for image in self.imagesByID.values():
            self.getDaemon().disconnect(image)

