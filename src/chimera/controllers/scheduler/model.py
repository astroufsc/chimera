from elixir import Entity, Field, using_options
from elixir import DateTime, Float, Integer, PickleType, Boolean, Text
from elixir import OneToMany, ManyToOne
from elixir import metadata, setup_all, create_all

from chimera.core.constants import DEFAULT_PROGRAM_DATABASE

class Program(Entity):
    using_options(tablename="programs")
    
    name   = Field(Text, default="Program")
    pi     = Field(Text, default="Anonymous Investigator")

    priority = Field(Integer, default=0)

    createdAt = Field(DateTime)
    finished  = Field(Boolean, default=False)
    
    actions      = OneToMany("Action", inverse="program")

    def __str__ (self):
        return "<Program #%d %s pi:%s #actions: %d>" % (self.id, self.name,
                                                        self.pi, len(self.actions))

class Action(Entity):
    using_options(tablename="action")

    program  = ManyToOne("Program", inverse="actions")

class AutoFocus(Action):
    using_options(tablename="action_focus", inheritance="multi")

    start   = Field(Integer, default=0)
    end     = Field(Integer, default=1)
    step    = Field(Integer, default=1)
    filter  = Field(Text, default=None)
    exptime = Field(Float, default=1.0)
    binning = Field(Text, default=None)
    window  = Field(Text, default=None)
    
class PointVerify(Action):
    using_options(tablename="action_pv", inheritance="multi")

    here   = Field(Boolean, default=None)
    choose = Field(Boolean, default=None) 

class Point(Action):
    using_options(tablename="action_point", inheritance="multi")

    targetRaDec = Field(PickleType, default=None)
    targetAltAz = Field(PickleType, default=None)
    targetName  = Field(Text, default=None)
    
class Expose(Action):
    using_options(tablename="action_expose", inheritance="multi")   

    filter     = Field(Text, default=None)
    frames     = Field(Integer, default=1)
    
    exptime    = Field(Integer, default=5)

    binning    = Field(Integer, default=None)
    window     = Field(Float, default=None)

    shutter    = Field(Text, default="OPEN")
    
    imageType  = Field(Text, default="")    
    filename   = Field(Text, default="$DATE-$TIME")
    objectName = Field(Text, default="")

db_file = DEFAULT_PROGRAM_DATABASE
metadata.bind = "sqlite:///%s" % db_file
metadata.bind.echo = False
setup_all()
create_all()
