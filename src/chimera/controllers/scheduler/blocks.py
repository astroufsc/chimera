
import time
import logging
import os
import string
import pyfits
import re
import glob

from chimera.core.version import _chimera_version_, _chimera_description_
from chimera.util.output import bold, green, red

def prepare_directory (directory, log=logging):
    save_on_temp = False

    # create dir if doesn't exists
    if not create_dir (directory):
        save_on_temp = True
        log.warning ("Couldn't create %s. Will try to save on /tmp." % directory)

    return save_on_temp

def create_dir (path):

    if os.path.exists (path):
        return True
    
    try:
        os.mkdir (path)
        return True
    except OSError, e:
        return False

def slew (tel, target, log=logging):

    slew_start = time.time ()
    log.info ("Slew started at %s" % time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(slew_start)))

    if target.obj.ra and target.obj.dec:
        tel.slewToRaDec (target.obj.ra, target.obj.dec)
    elif target.obj.alt and target.obj.az:
        tel.slewToAltAz (target.obj.al, target.obj.az)

    tel_position = tel.getPosition ()
    log.info ("Slew finished at %s (%f secs later)" % (time.strftime("%d/%m/%Y %H:%M:%S"), time.time()-slew_start))

    return tel_position

def change_filter (fw, target, log=logging):

    filter_start = time.time ()
    log.info ("Filter selection started at %s" % time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(filter_start)))

    fw.setFilter (target.filtername)

    filter_position = fw.getFilter ()

    log.info ("Filter selection finished at %s (%f secs later)" % (time.strftime("%d/%m/%Y %H:%M:%S"),
                                                                   time.time()-filter_start))

    return filter_position

def next_seq (dirname, filename, extension="fits"):

    fullpath = os.path.join (dirname, filename+"-")

    files = glob.glob (fullpath + "*")

    regexp = re.compile ("%s(?P<num>[0-9]+).%s" % (fullpath, extension))

    nums = [0]

    for name in files:

        match = regexp.match (name)

        if not match: continue

        try:
            num = int(match.groups()[0])
            nums.append (num)
        except ValueError:
            continue

    return max(nums)+1

def abort_exposure (cam):

    if not cam or not cam.isExposing():
        return False

    cam.abortExposure({})

    return True

def expose (cam, target, config={}, log=logging, term_event=None):

    if "filename" not in config:
        config["filename"] = "$date"

    if "dirname" not in config:
        config["dirname"] = os.getcwd()

    if "interval" not in config:
        config["interval"] = 0.0

    if "shutter" not in config:
        config["shutter"] = "open"

    if "display" not in config:
        config["display"] = True

    if "display_min_time" not in config:
        config["display_min_time"] = 5


    # DS9 setup

    has_ds9 = False

    if config["display"] and target.exptime >= config["display_min_time"]:

        try:
            from RO.DS9 import DS9Win as DS9
            has_ds9 = True
        except ImportError:
            log.warning (red("DS9 is not available. Display disabled"))
            
        if has_ds9:
            ds9 = DS9 (doRaise=True, doOpen=True)
    
    plan_start = time.time ()
    
    log.info ("#" * 50)
    log.info ("Start at %s" % time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(plan_start)))
    log.info ("#" * 50)        
    log.info ("Number of exposures: %s" % (target.nexp))
    log.info ("Integration time   : %s seconds" % (target.exptime))
    log.info ("#" * 50)    

    for i in range(int(target.nexp)):

        if term_event and term_event.isSet():
            return

        img_start = time.time ()
        log.info ("%s started  at %s" % ((bold("["+str(i+1) + "/" + str(target.nexp) + "]")),
                                         time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(img_start))))

        img = cam.expose ({"exp_time"	     : int(float(target.exptime)*100),
                           "shutter" 	     : config["shutter"],
                           "date_format"     : "%Y%m%d-%H%M%S",
                           "file_format"     : config["filename"],
                           "directory"	     : config["dirname"],
                           "save_on_temp"    : True,
                           "obj_name"        : string.replace (target.obj.name, ' ', '_').lower() or "unnamed",
                           "temp_regulation" : False})

        # aborting
        if not img and term_event.isSet():
            return False

        # camera error
        if not img:
            logging.warning (red("Something wrong. Check logs."))
            continue

        # Add some headers
        fp = pyfits.open (img, mode="update")
        hdu = fp[0]

        headers = [("OBSERVER", "fulano", "observer who acquired the data"),
                   ("ORIGIN", "OPD/LNA", "organization responsible for the data"),
                   ("OBJECT", target.obj.name or "object", "name of observed object"),
                   ("TELESCOP", "Meade 16inch", "name of the telescope"),
                   ("AIRMASS", 0, "air mass"),			       
                   ("RA", target.obj.ra or "-99 99 99", "right ascension of the observed object"),
                   ("DEC", target.obj.dec or "-99 99 99", "declination of the observed object"),
                   ("EXPTIME", float(target.exptime) or -1, "exposure time in seconds"),
                   ("EQUINOX", 2000.0, "equinox of celestial coordinate system"),
                   ("EPOCH", 2000.0, "equinox of celestial coordinate system"),
                   ("FILTER", target.filtername or "unknown", "name of filter used during the observation"),
                   ("CREATOR", _chimera_description_, ""),
                   ("SECPIX", 0.0, "plate scale")]

        for header in headers:
            hdu.header.update (*header)

        fp.flush ()
        fp.close ()

        log.info ("%s finished %s at %s (%f secs later)" % ((bold("["+str(i+1) + "/" + str(target.nexp) + "]")),
                                                            bold(os.path.basename(img)),
                                                            time.strftime("%d/%m/%Y %H:%M:%S"),
                                                            time.time()-img_start))

        # try to display the image
        if has_ds9 and config["display"] and target.exptime >= config["display_min_time"]:
            try:
                ds9.showFITSFile (img)
            except RuntimeError, e:
                #logging.exception(e)
                log.warning (red("[display] Can't display image."))

        if config["interval"] != 0 and (i+1) < target.nexp:
            log.info ("[waiting] %.0f seconds to begin next exposure." % config["interval"])
            time.sleep (config["interval"])

    log.info ("#" * 50)
    log.info ("Finished at %s: took %s seconds" % (time.strftime("%d/%m/%Y %H:%M:%S"), time.time()-plan_start))
    
            
