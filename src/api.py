import requests
import config

class OSRSPriceClient:
    def __init__(self):
        self.headers = {
            "User-Agent": config.USER_AGENT,
            "From": config.CONTACT,
        }
        self.session = requests.Session()

    def get_latest_prices(self) -> dict[int, dict]:
        resp = self.session.get(
            f"{config.BASE_URL}/latest",
            headers=self.headers,
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return {int(k): v for k, v in resp.json()["data"].items()}