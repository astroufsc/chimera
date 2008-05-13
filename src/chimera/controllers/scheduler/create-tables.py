from elixir import create_all, metadata

metadata.bind = "sqlite:///program.db"
metadata.bind.echo = True

from chimera.controllers.scheduler.model import *

create_all()

