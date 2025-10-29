from chimera.core.version import chimera_version


class TestVersion:
    def test_chimera_version(self):
        assert isinstance(chimera_version, str)
