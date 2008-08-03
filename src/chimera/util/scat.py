#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import subprocess
import tempfile
import logging
import os

from types import TupleType, IntType, FloatType

import asciidata

#logging.getLogger().setLevel(logging.DEBUG)


class SCatWrapper (object):

    __options__ = {"catalog": "-c %s",
                   "radius" : "-r %d",
                   "box"    : "-r %d,%d",
                   "near"   : "%s",
                   "limit"  : "-n %d",
                   "mag_faint"  : "-m%d ,%.2f",
                   "mag_both"   : "-m%d %.2f,%.2f",}


    # TODO: merge wirh _make_cmdline_args and simplify
    def _make_options_dict (self, conditions, bands):

        scat_options = {}

        # spatial limits
        if "box" in conditions and "radius" in conditions:
            raise TypeError("radius and box cannot be used together.")

        # scat use half-widths, we use full-width, so divide by 2.0 to satisfy scat
        if "box" in conditions:
            side = conditions.get("box")

            if not type(side) == TupleType:
                scat_options.update({"box": (side/2.0, side/2.0)})
            else:

                if len(side) >= 2:
                    scat_options.update({"box": (side[0]/2.0, side[1]/2.0)})
                else:
                    logging.warning ("Invalid box: %s" % side)
            
        if "radius" in conditions:
            scat_options.update({"radius": conditions.get("radius")})
            
        if "closest" in conditions:
            scat_options.update({"closest": True})
            try:
                del scat_options["radius"]
                del scat_options["box"]
            except KeyError: pass

        # magnitude limits
        mags = [(k.split("mag")[1], v) for k, v in conditions.items() if k.startswith("mag")]

        mag_faintest = None
        mag_brighter = None
        mag_band = None
        
        for mag, values in mags:
            if mag in bands:
                if type(values) == TupleType and len(values) >= 2:
                    mag_brighter = values[0]
                    mag_faintest = values[1]
                    mag_band = mag
                elif type(values) in (IntType, FloatType):
                    mag_band = mag
                    mag_faintest = values

                # scat only accept one magnitude limit
                break

        if mag_band:
            if mag_brighter:
                scat_options.update({"mag": (bands.index(mag_band), mag_brighter, mag_faintest)})
            elif mag_faintest:
                scat_options.update({"mag": (bands.index(mag_band), mag_faintest)})

        return scat_options

    # TODO: merge with _make_options_dict and simplify
    def _make_cmdline_args (self, options):

        catalog = "-c ucac2"
        params  = ""
        near    = "00:00:00 +00:00:00"

        if "catalog" in options:
            catalog = self.__options__["catalog"] % options.pop("catalog")

        if "near" in options:
            near = self.__options__["near"] % options.pop("near")

        if "mag" in options:
            values = options.pop("mag")
            
            if len(values) == 3:
                params += " " + self.__options__["mag_both"] % values
            elif len(values) == 2:
                params += " " + self.__options__["mag_faint"] % values

        if "closest" in options:
            value = options.pop("closest")
            params += " -a "

        # anyone else?
        for opt in options:

            if opt in self.__options__:
                try:
                    arg = self.__options__[opt] % options[opt]
                    params +=  " " + arg
                except ValueError:
                    pass

        return "%s %s %s" % (catalog, params, near)


    def _getTempFile (self):
        return tempfile.NamedTemporaryFile(mode='w+', prefix="chimera.scat", dir=tempfile.gettempdir())


    def run (self, options):

        # update options with the conditions given
        options.update (self._make_options_dict(options.pop("conditions", {}), options.pop("bands", [])))
        cmdline_args = self._make_cmdline_args(options)

        logging.debug ("Running scat with: %s arguments." % cmdline_args)

        # FIXME: who will close this file?
        result = self._getTempFile()

        try:
            proc = subprocess.Popen (args=cmdline_args.split(), executable="scat",
                                     env=options.get("env", os.environ), stderr=subprocess.STDOUT, stdout=result)
        except OSError:
            raise OSError("You don't have scat. Try put scat somewhere in your $PATH")

        proc.wait()

        try:

            data = asciidata.open(result.name)            
            data.toSExtractor()

            metadata = options.get("metadata", [])

            if metadata:
                for col, meta in zip(data, metadata):
                    col.rename(meta[0])
                    col.set_unit(meta[1])
                    col.set_colcomment(meta[2])

                data.flush()
                
            return  data
        
        except:
            
            return False
