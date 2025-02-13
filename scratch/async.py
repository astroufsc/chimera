class Readout:
    async def begin(self): ...

    async def complete(self): ...


class Exposure:
    async def begin(self): ...

    async def complete(self):
        return Readout()


class Proxy:
    def __init__(self, path): ...

    async def expose(self) -> Exposure:
        return Exposure()


async def f():
    camera = Proxy("/Camera/0")

    exposure = await camera.expose()

    await exposure.begin()

    readout = await exposure.complete()
    await readout.begin()
    await readout.complete()
