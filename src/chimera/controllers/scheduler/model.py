from elixir import Entity, Field, using_options
from elixir import DateTime, Float, Integer, PickleType, Boolean, Text
from elixir import OneToMany, ManyToOne
from elixir import metadata, setup_all


class Program(Entity):
    using_options(tablename='programs')
    
    caption     = Field(Text, default='Program')
    pi          = Field(Text, default='Anonymous Investigator')

    priority = Field(Integer, default=0)
    lastObservedAt = Field(DateTime)
    
    constraints  = OneToMany('Constraint', inverse='program')
    blocks       = OneToMany('Block', inverse='program')

class Constraint(Entity):
    using_options(tablename='constraints')
    
    type    = Field(Text)            
    min     = Field(Float, default=0)
    max     = Field(Float, default=0)
    
    program = ManyToOne('Program', inverse='constraints')
    block   = ManyToOne('Block', inverse='constraints')

class Block(Entity):
    using_options(tablename='blocks')

    program = ManyToOne('Program', inverse='blocks')

    begin = OneToMany('Action', inverse='block')
    end   = OneToMany('Action', inverse='block')

    constraints  = OneToMany('Constraint', inverse='block')    
    actions      = OneToMany('Action', inverse='block')

class Action(Entity):
    using_options(tablename='action')

    block = ManyToOne('Block', inverse='actions')
    finished = Field(Boolean, default=False)

class Focus(Action):
    using_options(tablename='action_focus', inheritance='multi')

class Reduce(Action):
    using_options(tablename='action_reduce', inheritance='multi')

class Point(Action):
    using_options(tablename='action_point', inheritance='multi')

    targetPos   = Field(PickleType, required=True)
    targetName  = Field(Text, default='Sky')            #(object FITS header)
    
class Expose(Action):
    using_options(tablename='action_expose', inheritance='multi')   

    filter      = Field(Text, default='CLEAR')      # ASCII value of filter to use
    frames      = Field(Integer, default=1)         # Frames to take
    
    exptime     = Field(Integer, default=5)                #Seconds per frame

    binX        = Field(Integer, default=1)                #X CCD Binning
    binY        = Field(Integer, default=1)                #Y CCD Binning
    
    windowX1 = Field(Float, default=0.0)
    windowX2 = Field(Float, default=1.0)
    windowY1 = Field(Float, default=0.0)
    windowY2 = Field(Float, default=1.0)
    
    shutterOpen = Field(Boolean, default=True)
    
    imageType   = Field(Text, default='object')    
    filename    = Field(Text, default='$DATE-$TIME')

# TODO: Better database creation scheme needed. Today, when model is
# imported, it will create all entities and tables as needed. We
# probably need to check if the database exists before trying to
# create it, to don't loose user's data.
metadata.bind = "sqlite:///program.db"
metadata.bind.echo = True
setup_all(create_tables=True)
