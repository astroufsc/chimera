def event(f):
    return f


class TelescopeSlew:

    ra: float
    dec: float

    position_ra_dec: tuple[float, float]
    position_alt_az: tuple[float, float]

    target_ra: float
    target_dec: float

    target_az: float
    target_alt: float

    target_ra_dec: tuple[float, float]
    target_alt_az: tuple[float, float]

    is_slewing: bool

    def slewToObject(self, name): ...
    def slewToRaDec(self, position): ...
    def slewToAltAz(self, position): ...
    def abortSlew(self): ...
    def moveEast(self, offset, rate): ...
    def moveWest(self, offset, rate): ...
    def moveNorth(self, offset, rate): ...
    def moveSouth(self, offset, rate): ...
    def moveOffset(self, offsetRA, offsetDec, rate): ...

    @event
    def slewBegin(self, target): ...
    @event
    def slewComplete(self, position, status): ...
