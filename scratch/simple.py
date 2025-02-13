from typing import cast
from rich import print
import os
import signal
import threading
import time

from chimera.core.event import event
from chimera.core.manager import Manager
from chimera.core.chimeraobject import ChimeraObject
from chimera.core.proxy import Proxy


def log(msg):
    d = {
        "thread": {
            "name": threading.current_thread().name,
            "native_id": threading.current_thread().native_id,
        },
        "process": {"pid": os.getpid()},
        "msg": msg,
    }
    print(d)


def log_all_threads(label: str):
    from rich.console import Console
    from rich.table import Table

    table = Table(title=f"Threads {label}")

    table.add_column("Name")
    table.add_column("ID", justify="right")

    for thread in threading.enumerate():
        table.add_row(thread.name, str(thread.native_id))

    console = Console()
    console.print(table)


class Instrument(ChimeraObject):
    def __init__(self):
        super().__init__()
        self.setHz(10)

    def do(self, n: int):
        time.sleep(n)
        self.completed(n)

    @event
    def completed(self, n: int): ...

    def control(self):
        log("step")
        return True


if __name__ == "__main__":
    m = Manager(host="127.0.0.1", port=9999)

    def signal_handler(sig, frame):
        m.shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    log_all_threads("after manager setup")

    m.addClass(Instrument, "unique")
    m.start("/Instrument/unique")

    log_all_threads("after instrument start")

    # THIS fails very hardly when location doesn't provide a valid port
    #      probably fails if no host is passed too
    p: Instrument = cast(Instrument, Proxy("localhost:9999/Instrument/unique"))

    def completed(n):
        log(f"Completed after {n} seconds")

    log("Calling do")

    log_all_threads("before calling Proxy")

    p.completed += completed
    p.do(1)

    m.shutdown()
    log_all_threads("after shutdown")
