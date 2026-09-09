import requests
import config

# --- OSRS API Client ---
class OSRSPriceClient:
    def __init__(self):
        self.headers = {
            "User-Agent": config.USER_AGENT,
            "From": config.CONTACT,
        }
        # Use a session to reuse TCP connections for better performance
        self.session = requests.Session()

    # Fetches the latest prices from the OSRS Wiki API and returns a dictionary mapping item IDs to their price data. Raises an exception if the request fails.
    def get_latest_prices(self) -> dict[int, dict]:
        resp = self.session.get(
            f"{config.BASE_URL}/latest",
            headers=self.headers,
            timeout=config.REQUEST_TIMEOUT,
        )
        """
        Fetches the latest prices from the OSRS Wiki API and returns a dictionary mapping item IDs to their price data. 
        Raises an exception if the request fails.
        """
        resp.raise_for_status()
        return {int(k): v for k, v in resp.json()["data"].items()}