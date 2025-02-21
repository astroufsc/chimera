from rich import print
from chimera.core.location import Location
from chimera.core.systemconfig import SystemConfig


def get_links(v):
    if isinstance(v, str):
        try:
            return [Location(v)]
        except Exception:
            return []

    if isinstance(v, list):
        try:
            return [Location(x) for x in v]
        except Exception:
            return []

    return []


print("digraph G {")

for filename in [
    "chimera.config_chimera",
    # "chimera.config_jype2",
    # "chimera.config_jype4",
    "chimera.config_supervisor",
    # "chimera.config_weather",
]:
    config = SystemConfig.fromFile(filename)

    site = config.sites[0]

    for instrument in config.instruments + config.controllers:
        myself = str(instrument)
        print(f'"{site}" -> "{myself}"')

        for k, v in instrument.config.items():
            if k == "device":
                continue
            links = get_links(v)
            # print(links)
            for link in links:
                print(f'"{myself}" -> "{link}"')

print("}")
