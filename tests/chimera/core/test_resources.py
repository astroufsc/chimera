import pytest

from chimera.core.resources import ResourcesManager


@pytest.fixture
def resources():
    return ResourcesManager()


class TestResources:
    def test_add(self, resources: ResourcesManager):
        assert len(resources) == 0

        resources.add("/Location/l1")
        assert len(resources) == 1

        # path already added
        with pytest.raises(ValueError):
            resources.add("/Location/l1")

        # FIXME: parse_url: tcp://127.0.0.1:6379//Telescope/0 fails because of the double bars

        resources.add("/Location/l2")
        assert len(resources) == 2

        with pytest.raises(ValueError):
            resources.add("Location/l1")

        with pytest.raises(ValueError):
            resources.add("/Location")

        with pytest.raises(ValueError):
            resources.add("//l1")

        with pytest.raises(ValueError):
            resources.add("/Location/")

        with pytest.raises(ValueError):
            resources.add("wrong location")

    def test_remove(self, resources: ResourcesManager):
        assert len(resources) == 0
        resources.add("/Location/l1")
        assert len(resources) == 1

        resources.remove("/Location/l1")

        assert len(resources) == 0
        assert "/Location/l1" not in resources

        with pytest.raises(KeyError):
            resources.remove("/What/l1")
        with pytest.raises(ValueError):
            resources.remove("wrong location")

    def test_get(self, resources: ResourcesManager):
        instance = object()
        resources.add("/Location/l1", instance)

        resource = resources.get("/Location/l1")

        assert resource is not None
        assert resource.path == "/Location/l1"
        assert resource.instance is instance

        assert resources.get("/Location/l99") is None
        assert resources.get("/OtherLocation/l1") is None

    def test_get_by_class(self, resources: ResourcesManager):
        class Base:
            pass

        class A(Base):
            pass

        class B(A):
            pass

        resources.add("/A/a", A())
        resources.add("/B/b", B())
        resources.add("/A/aa", A())
        resources.add("/B/bb", B())

        assert len(resources) == 4
        # get by class
        assert len(resources.get_by_class("Base")) == 4
        assert len(resources.get_by_class("A")) == 4
        assert len(resources.get_by_class("B")) == 2

    def test_get_by_index(self, resources: ResourcesManager):
        instance_l1 = object()
        instance_l2 = object()
        resources.add("/Location/l1", instance_l1)
        resources.add("/Location/l2", instance_l2)

        resource_l1 = resources.get("/Location/0")
        assert resource_l1 is not None
        assert resource_l1.path == "/Location/l1"

        resource_l2 = resources.get("/Location/1")
        assert resource_l2 is not None
        assert resource_l2.path == "/Location/l2"

        assert resources.get("/Location/9") is None
        assert resources.get("/LocationNotExistent/0") is None

        with pytest.raises(ValueError):
            resources.get("wrong location")

    def test_contains(self, resources: ResourcesManager):
        resources.add("/Location/l1")
        resources.add("/Location/l2")

        assert "/Location/l1" in resources
        assert "/Location/l2" in resources
        assert "/Location/0" in resources
        assert "/LocationNotExistent/l2" not in resources

    def test_dict_behavior(self, resources: ResourcesManager):
        resources.add("/Location/l2")
        resources.add("/Location/l1")

        expected_paths = list(resources.keys())
        expected_resources = list(resources.values())

        for k, v in resources.items():
            assert k == expected_paths.pop(0)
            assert v == expected_resources.pop(0)
