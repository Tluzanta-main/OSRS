"""
Central configuration for the OSRS Price Checker.
"""
from pathlib import Path

# --- OSRS Wiki Real-time Prices API ---
BASE_URL = "https://prices.runescape.wiki/api/v1/osrs"

# The API asks every client to identify itself so they can reach out if
# something's wrong with your usage.
USER_AGENT = "Price Checker/1.0"
CONTACT = "@tritonite5076 on Discord"

REQUEST_TIMEOUT = 10  # seconds

# --- Local data files (resolved relative to project root, not cwd) ---
PROJECT_ROOT = Path(__file__).parent.parent
ITEMS_FILE = PROJECT_ROOT / "items.json"
ITEMS_SETS_FILE = PROJECT_ROOT / "items_sets.json"

# --- Refresh behavior ---
REFRESH_INTERVAL_SECONDS = 30

# --- Staleness thresholds ---
STALENESS_THRESHOLD_SECONDS = 3600  # 1 hour 

# --- Grand Exchange tax constants ---
GE_TAX_NO_TAX_THRESHOLD = 50
GE_TAX_CAP = 5_000_000
GE_TAX_RATE = 0.02 
GE_TAX_RATE_MULTIPLIER = 1 - GE_TAX_RATE  # 0.98 

# --- Profit Margins ---
MIN_PROFIT_MARGIN = 100_000