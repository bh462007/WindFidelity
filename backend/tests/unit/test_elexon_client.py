
import pytest
import requests

from app.ingestion.elexon_client import ElexonClient


class FakeResponse:
    def __init__(self, data=None, status_error=None):
        self.data = data
        self.status_error = status_error

    def raise_for_status(self):
        if self.status_error:
            raise self.status_error

    def json(self):
        return self.data


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def mount(self, prefix, adapter):
        pass

    def get(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_fetch_json_returns_list():
    session = FakeSession(FakeResponse([{"generation": 100}]))
    client = ElexonClient(session=session)

    result = client.fetch_json("/forecast", {"format": "json"})

    assert result == [{"generation": 100}]
    assert session.calls[0][2] == 30


def test_fetch_json_unwraps_data_key():
    session = FakeSession(FakeResponse({"data": [{"generation": 100}]}))
    client = ElexonClient(session=session)

    assert client.fetch_json("/forecast", {}) == [{"generation": 100}]


@pytest.mark.parametrize("payload", [None, "invalid", [1, "bad"], {"other": []}])
def test_fetch_json_rejects_invalid_payload(payload):
    session = FakeSession(FakeResponse(payload))
    client = ElexonClient(session=session)

    with pytest.raises(ValueError, match="Unexpected response format"):
        client.fetch_json("/forecast", {})


def test_fetch_json_propagates_http_error():
    error = requests.HTTPError("502 Bad Gateway")
    session = FakeSession(FakeResponse(status_error=error))
    client = ElexonClient(session=session)

    with pytest.raises(requests.HTTPError):
        client.fetch_json("/forecast", {})


def test_fetch_json_propagates_connection_error():
    session = FakeSession(requests.ConnectionError("connection failed"))
    client = ElexonClient(session=session)

    with pytest.raises(requests.ConnectionError):
        client.fetch_json("/forecast", {})
