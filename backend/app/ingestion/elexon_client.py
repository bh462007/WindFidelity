
from datetime import date, timedelta

import pandas as pd
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.ingestion.schemas import normalize_fuelhh_records, validate_fuelhh_records

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
FUELHH_COLUMNS = ["businessType", "startTime", "quantity"]


def fetch_fuelhh(
    settlement_date_from: str,
    settlement_date_to: str | None = None,
    *,
    client: "ElexonClient | None" = None,
) -> pd.DataFrame:
    if client is None:
        client = ElexonClient()
    return client.fetch_fuelhh(settlement_date_from, settlement_date_to)


def fetch_windfor(start_time: str, *, client: "ElexonClient | None" = None) -> list[dict]:
    if client is None:
        client = ElexonClient()
    return client.fetch_windfor(start_time)


class ElexonClient:
    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: int = 10,
        session: Session | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or Session()

        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
        )

        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def fetch_json(self, endpoint: str, params: dict) -> list[dict]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        response = self.session.get(
            url,
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict):
            if "data" not in data:
                raise ValueError("Unexpected response format from Elexon")
            data = data["data"]

        if not isinstance(data, list) or not all(
            isinstance(item, dict) for item in data
        ):
            raise ValueError("Unexpected response format from Elexon")

        return data

    def fetch_fuelhh(
        self,
        settlement_date_from: str,
        settlement_date_to: str | None = None,
    ) -> pd.DataFrame:
        if settlement_date_to is None:
            settlement_date_to = settlement_date_from

        start_date = date.fromisoformat(settlement_date_from)
        end_date = date.fromisoformat(settlement_date_to)
        if end_date < start_date:
            raise ValueError("settlement_date_to must not be before settlement_date_from")

        normalized_records = []
        chunk_start = start_date
        while chunk_start <= end_date:
            chunk_end = min(chunk_start + timedelta(days=6), end_date)
            records = self.fetch_json(
                "/datasets/FUELHH",
                {
                    "settlementDateFrom": chunk_start.isoformat(),
                    "settlementDateTo": chunk_end.isoformat(),
                    "format": "json",
                },
            )
            validated = validate_fuelhh_records(records)
            normalized_records.extend(normalize_fuelhh_records(validated["valid_records"]))
            chunk_start = chunk_end + timedelta(days=1)

        return pd.DataFrame(normalized_records, columns=FUELHH_COLUMNS)

    def fetch_windfor(self, start_time: str) -> list[dict]:
        return self.fetch_json(
            "/forecast/generation/wind/evolution",
            {
                "startTime": start_time,
                "format": "json",
            },
        )
