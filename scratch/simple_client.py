from chimera.core.proxy import Proxy


def on_completed(n: int):
    print(f"Completed with {n}")


p = Proxy("localhost:9999/Instrument/unique")
p.completed += on_completed
p.do(2)

p.wait()
