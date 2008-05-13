
from chimera.controllers.scheduler.model import Constraint

from elixir.options import using_options


__all__ = ['MoonDistance', 'MoonPhase']


class MoonDistance (Constraint):

    using_options(tablename='constraint_moon_distance', inheritance='multi')    

    def satisfies (self, value):
        return True

class MoonPhase (Constraint):

    using_options(tablename='constraint_moon_phase', inheritance='multi')    

    def satisfies (self, value):
        return True
