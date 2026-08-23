"""
Manual smoke test: confirms api.py can reach the OSRS Wiki Real-time Prices
API and displays live prices for one set + its components from items_sets.json.

Run with: python test_api.py   (from inside src/)
"""
import json
import time

from rich.console import Console
from rich.table import Table

import config
from api import OSRSPriceClient

console = Console()


def load_sample_items() -> dict[str, int]:
    """Grab one set + its components from items_sets.json to test against."""
    sets_data = json.loads(config.ITEMS_SETS_FILE.read_text())

    first_category = next(iter(sets_data))                    # e.g. "Moons of Peril"
    first_set_name = next(iter(sets_data[first_category]))    # e.g. "Blood moon"
    first_set = sets_data[first_category][first_set_name]     # {"id":..., "components":{...}}

    sample = {first_set_name: first_set["id"]}
    sample.update(first_set["components"])
    return sample


def main():
    console.print(f"[cyan]Connecting to {config.BASE_URL} ...[/cyan]")

    client = OSRSPriceClient()

    start = time.perf_counter()
    try:
        prices = client.get_latest_prices()
    except Exception as exc:
        console.print(f"[bold red]Request failed:[/bold red] {exc}")
        return
    elapsed = time.perf_counter() - start

    console.print(f"[green]Success![/green] Got {len(prices)} items in {elapsed:.2f}s\n")

    sample_items = load_sample_items()

    table = Table(title="Sample Live Prices")
    table.add_column("Item", style="bold")
    table.add_column("ID", justify="right")
    table.add_column("Instant Buy (high)", justify="right")
    table.add_column("Instant Sell (low)", justify="right")

    for name, item_id in sample_items.items():
        info = prices.get(item_id)
        if info is None:
            table.add_row(name, str(item_id), "[dim]no data[/dim]", "[dim]no data[/dim]")
            continue
        high, low = info.get("high"), info.get("low")
        table.add_row(
            name,
            str(item_id),
            f"{high:,}" if high else "-",
            f"{low:,}" if low else "-",
        )

    console.print(table)


if __name__ == "__main__":
    main()