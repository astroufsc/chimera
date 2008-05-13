
from chimera.controllers.scheduler.model import Program

from elixir.options import using_options


__all__ = ['NonPeriodicProgram',
           'PeriodicProgram']


class NonPeriodicProgram (Program):

    using_options(tablename='program_non_periodic', inheritance='multi')

class PeriodicProgram (Program):

    using_options(tablename='program_periodic', inheritance='multi')

