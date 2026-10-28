
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


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

    def fetch_fuelhh(self, settlement_date: str) -> list[dict]:
        return self.fetch_json(
            "/datasets/FUELHH",
            {
                "settlementDateFrom": settlement_date,
                "settlementDateTo": settlement_date,
                "format": "json",
            },
        )

    def fetch_windfor(self, start_time: str) -> list[dict]:
        return self.fetch_json(
            "/forecast/generation/wind/evolution",
            {
                "startTime": start_time,
                "format": "json",
            },
        )
