
from elixir import setup_all, metadata

from chimera.controllers.scheduler.program import *

from chimera.controllers.scheduler.exposures import *
from chimera.controllers.scheduler.constraints import *

setup_all()

metadata.bind = "sqlite:///program.db"
#metadata.bind.echo = True
