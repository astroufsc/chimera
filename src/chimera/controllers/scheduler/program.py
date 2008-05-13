
__all__ = ['Program', 'Observation', 'Constraint',
           'Target', 'Exposure', 'Calibration',
           'setup_all', 'create_all', 'session']


from elixir import *

from datetime import datetime


class Program (Entity):

    using_options(tablename='program')

    pi = Field(String(50), required=True)
    constraints  = OneToMany('Constraint')
    observations = OneToMany('Observation')

    history = OneToMany('History')
    
    created  = Field(DateTime, required=True, default=datetime.now)
    modified = Field(DateTime, required=True, default=datetime.now)
    finished = Field(Boolean, required=True, default=False)

    def touch (self):
        self.modified = datetime.now()
        self.flush()

    def finish (self):
        self.finished = True
        self.flush()

    def timespan (self):
        span = sum([obs.timespan() for obs in self.observations])

class Observation (Entity):

    using_options(tablename='observation')    

    program = ManyToOne('Program')

    constraints = OneToMany('Constraint')

    target    = OneToOne('Target')
    exposures = OneToMany('Exposure')

    def complete (self):
        return all([exp.complete for exp in self.exposures])

    def timespan (self):
        span = 0
        for exp in self.exposures:
            span += exp.framesLeft * exp.exptime
            if exp.interval:
                span += exp.interval * (exp.framesLeft-1)
        return span

            
class Calibration (Observation):

    using_options(tablename='calibration', inheritance='multi')


class Constraint (Entity):

    using_options(tablename='constraint', inheritance='multi')    

    belongs_to('program', of_kind='Program')
    belongs_to('observation', of_kind='Observation')

    has_field('name', String(50), required=True)
    has_field('min', Float, required=False)
    has_field('max', Float, required=False)

    def satisfies (self, value):
        return False


class Target (Entity):

    using_options(tablename='target')    

    observation = ManyToOne('Observation')
    
    name     = Field(String(50), required=True)
    position = Field(PickleType)


class Exposure (Entity):

    using_options(tablename='exposure', inheritance='multi')
    
    observation = ManyToOne('Observation')

    exptime = Field(Float, required=True, default=1.0)
    filter_ = Field(String(20), required=False, default="V")
    frames  = Field(Integer, required=False, default=1)
    interval= Field(Float, required=False, default=0.0)

    framesDone = Field(Integer, required=True, default=0)
    framesLeft = property(lambda self: self.frames - self.framesDone)

    def complete (self):
        return False

    def process (self):
        pass

class History (Entity):

    using_options(tablename='history')

    program = ManyToOne('Program')

    when    = Field(DateTime, required=True, default=datetime.now)
    who     = Field(Text, required=True, default="scheduler")
    message = Field(Text, required=True)
