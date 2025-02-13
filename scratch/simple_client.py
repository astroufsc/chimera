from chimera.core.proxy import Proxy


if __name__ == "__main__":
    p = Proxy("localhost:9999/Instrument/unique")
    # p.completed += lambda n: print(f"Completed after {n} seconds")
    p.do(2)
