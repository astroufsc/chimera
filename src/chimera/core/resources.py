# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2006-present Paulo Henrique Silva <ph.silva@gmail.com>

import time
from concurrent.futures import Future
from dataclasses import dataclass, field
from typing import Any

from chimera.core.url import parse_path


@dataclass
class Resource:
    path: str
    cls: str
    name: str | int
    instance: Any | None = None
    bases: list[str] = field(default_factory=list[str])
    created: float = field(default_factory=time.monotonic)
    loop: Future[bool] | None = None


class ResourcesManager:
    def __init__(self):
        self._res = {}

    def add(
        self, path: str, instance: Any | None = None, loop: Future[bool] | None = None
    ) -> None:
        cls, name = parse_path(path)
        if path in self:
            raise ValueError(f"'{path}' already exists.")

        resource = Resource(path=path, cls=cls, name=name)
        resource.instance = instance
        if resource.instance is not None:
            resource.bases = [b.__name__ for b in type(resource.instance).mro()]
        resource.loop = loop

        self._res[path] = resource

    def remove(self, path: str) -> None:
        if path not in self:
            raise KeyError(f"{path} not found")

        del self._res[path]

    def get(self, path: str) -> Resource | None:
        cls, name = parse_path(path)
        if isinstance(name, int):
            return self._get_by_index(cls, name)
        return self._get(cls, name)

    def get_by_class(self, cls: str) -> list[Resource]:
        resources = []

        for k, v in list(self._res.items()):
            if cls == v.cls or cls in v.bases:
                resources.append(self._res[k])

        resources.sort(key=lambda entry: entry.created)
        return resources

    def _get_by_index(self, cls: str, index: int) -> Resource | None:
        resources = self.get_by_class(cls)
        if not resources or index > len(resources):
            return None
        return self._res[resources[index].path]

    def _get(self, cls: str, name: str) -> Resource | None:
        path = f"/{cls}/{name}"

        resources = self.get_by_class(cls)
        for resource in resources:
            if resource.path == path:
                return resource
        return None

    def __contains__(self, path: str):
        return self.get(path) is not None

    def __len__(self):
        return len(self._res)

    def items(self):
        return self._res.items()

    def keys(self):
        return iter(self._res.keys())

    def values(self):
        return iter(self._res.values())
