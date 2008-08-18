
from glob import glob
import os

from pyraf import iraf

from chimera.core.chimeraobject import ChimeraObject
import calibration
import reduction_tools


class Reduction(ChimeraObject):
    """Don't need to know where the data is coming from.
        The data file (with directory) will be passed to the pipeline.
        The user only has to configure where the file will go.
    """
    
    __config__ = {"calibration_dir": "/data/calibration/",
                  "subset"         : "filter"                  
                  }
    
    def __init__(self):
        ChimeraObject.__init__(self)
             
             
    def __start__(self):
        
        self.imagedate = '060808'
        self.reduction_dir = self["calibration_dir"]+'Today/'
             
    def __stop__(self):
        pass
    
    
    def _processScienceIm(self, input, masterdir):        
        """Takes in science images to be reduced, checks that they are in fact science images,
        then calls to the iraf task ccdproc to reduce the science images.  Input can be a file location
        or a directory.
        
        @param input: file or directory location of science images to be reduced
        @type input: str
        @param masterdir: directory location of master calibration images
        @type masterdir: str
        """
        
        sciencelist = []
        reducedlist = None
        
        
        if os.path.isfile(input):
            
            if os.path.splitext(os.path.split(input)[-1])[-1]=='.fits':
                iraf.images.imutil.imgets(image=input, param='imagetyp')
                imagetyp = iraf.images.imutil.imgets.value
                if imagetyp=='object':
                    sciencelist.append(input)
            
            sciencelist = reduction_tools.copyNewFits(sciencelist, os.path.split(input)[0]+'/ReducedImages/')
            
            for im in sciencelist:
                iraf.noao.imred.ccdred.ccdproc(images=im, fixpix='no', oversca='no', trim='no', zero=masterdir+'Zero', dark=masterdir+'Dark', flat=masterdir+'Flat*')
                os.remove(input)
            
            reducedlist = sciencelist
        
        
        elif os.path.isdir(input):
            
            for im in glob(input+'/*'):
                if os.path.splitext(os.path.split(im)[-1])[-1]=='.fits':
                    iraf.images.imutil.imgets(image=im, param='imagetyp')
                    imagetyp = iraf.images.imutil.imgets.value
                    if imagetyp=='object':
                        sciencelist.append(im)
                   
            sciencelist = reduction_tools.copyNewFits(sciencelist, input+'ReducedImages/')
            
            for im in sciencelist:
                iraf.noao.imred.ccdred.ccdproc(images=im, fixpix='no', oversca='no', trim='no', zero=masterdir+'Zero',dark=masterdir+'Dark', flat=masterdir+'Flat*')
                os.remove(input+os.path.split(im)[-1])
                
            reducedlist = sciencelist
            
        
        
                    
        
        return reducedlist
               
    
    def _createMasters(self, zero='yes', dark='yes', flat='yes'):
        """Calls to the calibration module to create master calibration images.
        zero, dark, and flat are set to 'yes,' but can be set to 'no' if any of those
        are not desired.
        """
        
        True = 'yes'
        False = 'no'
        
        while(1):
            if not zero and dark and flat:
                break
            masters = calibration.Calibration(self.reduction_dir)
            reduction_tools.makeDir(self.reduction_dir+'Masters/')
            if zero:
                masters.makeZero()
            if dark:
                masters.makeDark()
            if flat:
                masters.makeFlat()
            break
                
   
    def _haveMasters(self, checkdirectory):
        """A check for the existence of master calibration images.
        """

        if not os.path.isdir(checkdirectory+'Masters/'):
            return False
        ## Currently only checks for the existence of a master directory.
        ## Future work may be to add a check for individual masters.
        else:
            return True
                   
        
    def reduce(self, input, coordsList=None, subset='filter'):
        """The method in the pipeline that performs the complete reduction.  Input
        should first be a directory containing at least the calibration images.  Science
        images to be reduced can also be included.  Can also pass just a filename as input, however
        single images passed in can only be science images.  Nothing will be done if just a single 
        calibration images is passed.
        
        @param input: directory where calibration and science images are stored or filename of an image to be reduced.
        @type input: str
        @param coordsList: future work: will give a set of coordinates for photometry
        @type coordsList: list
        @param subset: subset by which to reduce science images.  Default is filter.  If this is changed, it must be present in the headers to take effect.
        @type subset: str
        
        @return: images that have been reduced. the images are given as the location in the 'ReducedImages/' directory, which is automatically created.
        @rtype: list
        
        """
        
        self.imagedate = os.path.split(os.path.split(input)[0])[-1]
        print os.path.split(input)[0]
        print self.imagedate
        
        self.reduction_dir = self["calibration_dir"]+self.imagedate+'/'
        
        masterdir = self.reduction_dir+'Masters/'
                                
        
        if os.path.isfile(input):
            
            imagelist = []
            filename = os.path.split(input)[-1]
            imagelist.append(input)
            reduction_tools.copyNewFits(imagelist, self.reduction_dir)
            
            if not self._haveMasters(self.reduction_dir):
                print "No master calibration images found for this date."
                return None
                        
            else:
                
                subset_file = open(self.reduction_dir+'instruments', 'w')
                print >> subset_file, "subset   %s" % subset
                subset_file.close()
                    
                reduced_images = self._processScienceIm(self.reduction_dir+filename, masterdir)
                return reduced_images
            
             
        elif os.path.isdir(input):
            print input
            
            copylist = glob(input+'*')
            
            reduction_tools.copyNewFits(copylist, self.reduction_dir)
            
            subset_file = open(self.reduction_dir+'instruments', 'w')
            print >> subset_file, "subset   %s" % subset
            subset_file.close()            
            
            if not self._haveMasters(self.reduction_dir):
                self._createMasters()
               
            reduced_images = self._processScienceIm(self.reduction_dir, masterdir)
            return reduced_images
                
                       
        else:
            
            self.err.info("Input is not a valid input type")
            return None
        
 
        
        
        
        
        
    
    
    