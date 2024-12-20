from enum import StrEnum


class Enum(StrEnum):
    def __getitem__(self, name):
        return super().__getitem__(name.split(".")[-1])
