from chimera.core.version import _chimera_version_


class TestVersion:
    assert isinstance(_chimera_version_, str)
    pass
