from enum import StrEnum


class Enum(StrEnum):
    def __getitem__(self, name):
        # still needed for serialization - fixme
        return super().__getitem__(name.split(".")[-1])
