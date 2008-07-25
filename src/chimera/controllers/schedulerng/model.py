from elixir import Entity, Field, using_options
from elixir import DateTime, Float, Integer, UnicodeText, PickleType, Boolean, Text
from elixir import OneToMany, ManyToOne, ManyToMany
from elixir import metadata, setup_all

from datetime import datetime
from chimera.util.position import Position

from chimera.core.log import logging

import logging
import time

from chimera.core.exceptions import ObjectNotFoundException
from chimera.interfaces.camera  import Shutter, Binning, Window

class Constraint(Entity):
    using_options(tablename='constraints')
    
    caption = Field(UnicodeText, default='Constraint')        #Constraint name (specified by PI)
    type    = Field(UnicodeText)        #Module providing constraint logic
    min     = Field(Float, default=0)              #Minimum value passed to constraint logic
    max     = Field(Float, default=0)              #Maximum value passed to constraint logic
    
    exposure = ManyToOne('Exposure', inverse='constraints')
    observation = ManyToOne('Observation', inverse='constraints')
    program = ManyToOne('Program', inverse='constraints')
    
    def checkMe(self):
        return True
    
class Exposure(Entity):
    using_options(tablename='exposures')

    filter      = Field(UnicodeText, default=u'CLEAR')      #ASCII value of filter to use
    frames      = Field(Integer, default=1)                #Frames to take
    
    duration    = Field(Integer, default=5)                #Seconds per frame

    binX        = Field(Integer, default=1)                #X CCD Binning
    binY        = Field(Integer, default=1)                #Y CCD Binning
    
    windowXCtr  = Field(Float, default=0.5)
    windowYCtr  = Field(Float, default=0.5)
    windowWidth = Field(Float, default=1.0)
    windowHeight= Field(Float, default=1.0)
    
    shutterOpen = Field(Boolean, default=True)
    
    imageType   = Field(UnicodeText, default=u'OBJECT')
    
    priority    = Field(Integer, default=1000)    
    
    finished   = Field(Boolean, default=False)            #Observation finished
    
    constraints = OneToMany('Constraint', inverse='exposure')
    
    observation = ManyToOne('Observation', inverse='exposures')

class Observation(Entity):
    using_options(tablename='observations')
    
    caption     = Field(UnicodeText, default=u'Observation')
    timeBetweenExposuresMin     = Field(Integer, default=0)     #Seconds!
    timeBetweenExposuresMax     = Field(Integer, default=0)     #Seconds!
    lastExposureAt              = Field(DateTime)
    priority    = Field(Integer, default=1000)
    
    targetPos   = Field(PickleType, required=True)
    targetName  = Field(UnicodeText, default='Sky')            #(object FITS header)
    
    mapRAcount  = Field(Integer, default=1)     #Map cells along RA
    mapDECcount = Field(Integer, default=1)     #Map cells along DEC
    mapRAsize   = Field(Float, default=2.7777777777777779e-05)                  #Distance between center of cells along RA [deg]
    mapDECsize  = Field(Float, default=2.7777777777777779e-05)                  #Distance between center of cells along DEC [deg]
    mapLoops    = Field(Integer, default=1)     #Number of times to loop through map
    
    constraints = OneToMany('Constraint', inverse='observation')
    
    exposures   = OneToMany('Exposure', inverse='observation')
    program     = ManyToOne('Program', inverse='observations')
    
class Program(Entity):
    using_options(tablename='programs')
    
    caption     = Field(UnicodeText, default=u'Program')
    pi          = Field(UnicodeText, default=u'Anonymous Investigator')
    priority    = Field(Integer, default=1000)
    
    timeBetweenObservationsMin  = Field(Integer, default=0)     #Seconds!
    timeBetweenObservationsMax  = Field(Integer, default=0)     #Seconds!
    lastObservationAt   = Field(DateTime)
    
    constraints = OneToMany('Constraint', inverse='program')
    
    observations= OneToMany('Observation', inverse='program')

class Setting(Entity):
    using_options(tablename='settings')
    
    name        = Field(Text, primary_key=True)
    txtValue    = Field(Text, default=True)
    

metadata.bind = "sqlite:///program.db"
metadata.bind.echo = True
setup_all(True)
