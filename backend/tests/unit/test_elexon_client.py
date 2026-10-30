
import pandas as pd
import pytest
import requests

from app.ingestion.elexon_client import ElexonClient, fetch_fuelhh, fetch_windfor


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
        self.adapters = {}

    def mount(self, prefix, adapter):
        self.adapters[prefix] = adapter

    def get_adapter(self, prefix):
        return self.adapters[prefix]

    def get(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class SequencedSession(FakeSession):
    def __init__(self, responses):
        super().__init__(None)
        self.responses = iter(responses)

    def get(self, url, params, timeout):
        self.calls.append((url, params, timeout))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def fuelhh_record(start_time, fuel_type="WIND", generation=1234):
    return {
        "dataset": "FUELHH",
        "publishTime": "2026-10-27T00:00:00Z",
        "startTime": start_time,
        "settlementDate": start_time[:10],
        "settlementPeriod": 1,
        "fuelType": fuel_type,
        "generation": generation,
    }


def test_fetch_json_returns_list():
    session = FakeSession(FakeResponse([{"generation": 100}]))
    client = ElexonClient(session=session)

    result = client.fetch_json("/forecast", {"format": "json"})

    assert result == [{"generation": 100}]
    assert session.calls[0][2] == 10


def test_fetch_fuelhh_uses_expected_parameters():
    session = FakeSession(FakeResponse([
        {
            "dataset": "FUELHH",
            "publishTime": "2026-10-27T00:00:00Z",
            "startTime": "2026-10-26T23:30:00Z",
            "settlementDate": "2026-10-26",
            "settlementPeriod": 48,
            "fuelType": "WIND",
            "generation": 1234,
        }
    ]))
    client = ElexonClient(session=session)

    result = client.fetch_fuelhh("2026-10-26")

    expected = pd.DataFrame([
        {
            "businessType": "Wind generation",
            "startTime": "2026-10-26T23:30:00Z",
            "quantity": 1234.0,
        }
    ])

    assert result.equals(expected)
    assert session.calls[0][0].endswith("/datasets/FUELHH/stream")
    assert session.calls[0][1] == {
        "settlementDateFrom": "2026-10-26",
        "settlementDateTo": "2026-10-26",
        "format": "json",
    }
    assert session.calls[0][2] == 10


def test_fetch_fuelhh_uses_stream_endpoint_for_full_date_range():
    session = FakeSession(FakeResponse([]))
    client = ElexonClient(session=session)

    result = client.fetch_fuelhh("2026-01-01", "2026-01-31")

    assert result.empty
    assert len(session.calls) == 1
    assert session.calls[0][0].endswith("/datasets/FUELHH/stream")
    assert session.calls[0][1] == {
        "settlementDateFrom": "2026-01-01",
        "settlementDateTo": "2026-01-31",
        "format": "json",
    }


def test_fetch_fuelhh_filters_and_normalizes_wind_records():
    session = FakeSession(FakeResponse([
        fuelhh_record("2026-01-01T00:00:00Z"),
        fuelhh_record("2026-01-01T00:30:00Z", fuel_type="SOLAR"),
        fuelhh_record("2026-01-08T00:00:00Z", generation=5678),
    ]))
    client = ElexonClient(session=session)

    result = client.fetch_fuelhh("2026-01-01", "2026-01-31")

    assert result.to_dict("records") == [
        {
            "businessType": "Wind generation",
            "startTime": "2026-01-01T00:00:00Z",
            "quantity": 1234.0,
        },
        {
            "businessType": "Wind generation",
            "startTime": "2026-01-08T00:00:00Z",
            "quantity": 5678.0,
        },
    ]
    assert len(session.calls) == 1


def test_fetch_fuelhh_handles_empty_response_with_expected_columns():
    session = FakeSession(FakeResponse([]))
    client = ElexonClient(session=session)

    result = client.fetch_fuelhh("2026-01-01", "2026-01-31")

    assert result.empty
    assert list(result.columns) == [
        "businessType",
        "startTime",
        "quantity",
    ]


def test_fetch_fuelhh_propagates_http_error():
    error = requests.HTTPError("502 Bad Gateway")
    session = FakeSession(error)
    client = ElexonClient(session=session)

    with pytest.raises(requests.HTTPError, match="502 Bad Gateway"):
        client.fetch_fuelhh("2026-01-01", "2026-01-31")

    assert len(session.calls) == 1


def test_fetch_windfor_uses_expected_parameters():
    session = FakeSession(FakeResponse([{"generation": 100}]))
    client = ElexonClient(session=session)

    result = client.fetch_windfor("2026-10-26T00:00:00Z")

    assert result == [{"generation": 100}]
    assert session.calls[0][0].endswith("/forecast/generation/wind/evolution")
    assert session.calls[0][1] == {
        "startTime": "2026-10-26T00:00:00Z",
        "format": "json",
    }
    assert session.calls[0][2] == 10


def test_module_level_fetch_helpers_are_public_and_work():
    fuel_session = FakeSession(FakeResponse([
        {
            "dataset": "FUELHH",
            "publishTime": "2026-10-27T00:00:00Z",
            "startTime": "2026-10-26T23:30:00Z",
            "settlementDate": "2026-10-26",
            "settlementPeriod": 48,
            "fuelType": "WIND",
            "generation": 1234,
        }
    ]))
    wind_session = FakeSession(FakeResponse([{"generation": 100}]))

    fuelhh = fetch_fuelhh(
        "2026-10-26",
        client=ElexonClient(session=fuel_session),
    )
    assert fuelhh.equals(pd.DataFrame([
        {
            "businessType": "Wind generation",
            "startTime": "2026-10-26T23:30:00Z",
            "quantity": 1234.0,
        }
    ]))

    wind_result = fetch_windfor(
        "2026-10-26T00:00:00Z",
        client=ElexonClient(session=wind_session),
    )
    assert wind_result == [{"generation": 100}]


def test_retry_policy_matches_intended_configuration():
    client = ElexonClient(session=FakeSession(FakeResponse([{"generation": 100}])))
    adapter = client.session.get_adapter("https://")
    retry = adapter.max_retries

    assert retry.total == 3
    assert retry.backoff_factor == 1
    assert retry.status_forcelist == (429, 500, 502, 503, 504)
    assert retry.allowed_methods == frozenset({"GET"})
    assert retry.respect_retry_after_header is True


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
