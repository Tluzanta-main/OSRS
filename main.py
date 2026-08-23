import json
import time
from rich.console import Console
from rich.live import Live
from rich.table import Table

import config
from api import OSRSPriceClient
from calculate_sets import SetProfitCalculator




console = Console()

# Read the sets data from the JSON file and return it as a dictionary
def load_sets_data() -> dict: 
    return json.loads(config.ITEMS_SETS_FILE.read_text())

def format_seconds(seconds: int | None) -> str:
    """e.g. 45 -> '45s', 187 -> '3m 7s', 7300 -> '2h 1m'"""
    if seconds is None:
        return "-"
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"

# Table for displaying the profit calculations in a rich format
# p is an instance of SetProfit
def build_table_full_set(profits) -> Table: 
    known = [p for p in profits if not p.missing_data]
    known.sort(key=lambda p: p.net_profit or 0, reverse=True)

    table = Table(title="OSRS Set Flip Profit Calculator")
    table.add_column("Category", style="bold")
    table.add_column("Set", style="bold")
    table.add_column("Component Cost", justify="right")
    table.add_column("Set Sell Price", justify="right")
    table.add_column("Tax", justify="right")
    table.add_column("Net Profit", justify="right")
    table.add_column("Margin %", justify="right")
    table.add_column("Timestamp (sec)", justify="right")

    for p in known: 
        color = "green" if p.net_profit and p.net_profit > 100_000 else "red"
        table.add_row(
            p.category,
            p.set_name,
            f"{p.component_cost:,}" if p.component_cost is not None else "-",
            f"{p.set_sell_price:,}" if p.set_sell_price is not None else "-",
            f"{p.tax:,}" if p.tax is not None else "-",
            f"[{color}]{p.net_profit:,}[/{color}]" if p.net_profit is not None else "-",
            f"{p.margin_pct:.2f}%" if p.margin_pct is not None else "-",
            f"{format_seconds(p.age_total_set)}" if p.age_total_set is not None else "-",
        )

    missing = len(profits) - len(known)
    if missing: 
        table.caption = f"{missing} sets(s) skipped - missing price data" 

    return table

def main(): 
    sets_data = load_sets_data()
    client = OSRSPriceClient()
    calculator = SetProfitCalculator(client)

    console.print(f"[cyan]Starting live price feed - press Ctrl+C to stop...[/cyan]")

    try: 
        with Live(console=console, refresh_per_second=10) as live: 
            while True: 
                try: 
                    profits = calculator.calculate_all_sets(sets_data)
                    live.update(build_table_full_set(profits))
                except Exception as e: 
                    console.print(f"[red]Error refreshing prices: {e}[/red]")
                time.sleep(config.REFRESH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")

if __name__ == "__main__":
    main()