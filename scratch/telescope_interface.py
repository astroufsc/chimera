import enum
import json

import pydantic


class Coord: ...


class Position: ...


# FIXME: migrate to state machine status?
class TelescopeStatus(enum.StrEnum):
    OK = "OK"
    ERROR = "ERROR"
    ABORTED = "ABORTED"
    OBJECT_TOO_LOW = "OBJECT_TOO_LOW"
    OBJECT_TOO_HIGH = "OBJECT_TOO_HIGH"


def event(func):
    return func


class SlewRate(enum.Enum):
    MAX = 0
    GUIDE = 1


class AlignMode(enum.Enum):
    POLAR = 0
    ALT_AZ = 1


class Interface[C, T](pydantic.BaseModel):
    config: C
    telemetry: T


class Fan(Interface): ...


class Config(pydantic.BaseModel): ...


class TelescopeConfig(Config):
    device: str | None = None
    model: str = "Fake Telescopes Inc."
    optics: list = ["Newtonian", "SCT", "RCT"]
    mount: str = "Mount type Inc."
    aperture: float = 100.0
    focal_length: float = 1000.0
    focal_reduction: float = 1.0
    fans: list[Fan] = []


class Telescope[C, T](Interface[C, T]): ...


class TelescopeSlewConfig(TelescopeConfig):
    timeout: int = 30
    slew_rate: SlewRate = SlewRate.MAX
    auto_align: bool = True
    align_mode: AlignMode = AlignMode.POLAR
    slew_idle_time: float = 0.1
    max_slew_time: float = 90.0
    stabilization_time: float = 2.0
    position_sigma_delta: float = 60.0
    skip_init: bool = False
    min_altitude: int = 20


class TelescopeSlewTelemetry(TelescopeConfig):
    timeout: int = 30


class TelescopeSlew(Telescope[TelescopeSlewConfig, TelescopeSlewTelemetry]):

    def slew_to_object(self, name: str): ...

    # FIXME: should return something
    #        is this sync or async? always async for actions?
    def slew_to_ra_dec(self, position: Position): ...

    def slew_to_alt_az(self, position: Position): ...

    def abort_slew(self): ...

    def is_slewing(self) -> bool: ...

    # FIXME: encode and/or accept different units, right now it is interpreted as arcseconds
    def move_east(self, offset: float | int, rate=SlewRate.MAX): ...

    def move_west(self, offset: float | int, rate=SlewRate.MAX): ...

    def move_north(self, offset: float | int, rate=SlewRate.MAX): ...

    def move_south(self, offset: float | int, rate=SlewRate.MAX): ...

    def move_offset(
        self, offset_ra: float | int, offset_dec: float | int, rate=SlewRate.GUIDE
    ): ...

    def get_ra(self) -> Coord: ...

    def get_dec(self) -> Coord: ...

    def get_az(self) -> Coord: ...

    def get_alt(self) -> Coord: ...

    def get_position_ra_dec(self) -> Position: ...

    def get_position_alt_az(self) -> Position: ...

    def get_target_ra_dec(self) -> Position: ...

    def get_target_alt_az(self) -> Position: ...

    @event
    def slew_begin(self, target: Position) -> None: ...

    @event
    def slew_complete(self, position: Position, status: TelescopeStatus) -> None: ...


if __name__ == "__main__":
    print(json.dumps(TelescopeSlew.model_json_schema()))
