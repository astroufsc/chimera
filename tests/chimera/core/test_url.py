import pytest

from chimera.core.url import URL, InvalidHostError, InvalidPathError, parse_url


class TestURL:
    def test_parse_url(self):
        url = parse_url("hostname:1000/Class/name")
        assert url

        assert url.host == "hostname"
        assert url.port == 1000
        assert url.cls == "Class"
        assert url.name == "name"

    def test_copy_ctor(self):
        url_1 = parse_url("hostname:1000/Class/name")
        url_2 = parse_url(url_1)

        assert url_1
        assert url_2

        assert url_1.host == url_2.host
        assert url_1.port == url_2.port
        assert url_1.cls == url_2.cls
        assert url_1.name == url_2.name

        assert id(url_1) == id(url_2)

    def test_eq(self):
        url_1 = parse_url("host.com.br:1000/Class/name")
        url_2 = parse_url("host.com.br:1000/Class/name")

        assert hash(url_1) == hash(url_2)
        assert url_1 == url_2

    @pytest.mark.parametrize(
        "url",
        [
            "200.100.100.100:1000/Class/other",
            "200.100.100.100:1000/Class/1",
            "localhost:9000/class/o",
        ],
    )
    def test_valid(self, url: str):
        new_url = parse_url(url)
        assert new_url is not None
        assert isinstance(new_url, URL)

    @pytest.mark.parametrize(
        "url",
        [
            "/Class/name",
            "200.100.100.100/Class/name",
            ":1000/Class/name",
            "200.100.100.100:port/Class/name",
        ],
    )
    def test_invalid_host(self, url: str):
        with pytest.raises(InvalidHostError):
            parse_url(url)

    @pytest.mark.parametrize(
        "url",
        [
            "200.100.100.100:1000  /  Class   /   other   ",  # spaces matter.
            "200.100.100.100:1000/Who/am/I",
            "200.100.100.100:1000/Who",
            "200.100.100.100:1000/1234/name",
            "200.100.100.100:1000/12345Class/o",
            "200.100.100.100:1000/Class/1what",
        ],
    )
    def test_invalid_path(self, url: str):
        with pytest.raises(InvalidPathError):
            parse_url(url)
