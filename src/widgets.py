from textual.widgets import DataTable
import config   

"""
    Formats seconds into a human-readable string representation, 
    converting seconds into hours, minutes, and seconds as appropriate.
    If the input is None, it returns a dash ("-") to indicate missing data.
"""
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

class SummaryTable(DataTable):
    """
    A table widget for displaying summary information about the sets. 
    """

    """
    Definition of the SummaryTable class, which inherits from DataTable. 
    This class is used to display summary information about the sets in a tabular format.
    """
    def on_mount(self) -> None:
        self.add_columns(
            "Category","Set","Component Cost","Set Sell Price","Tax","Net Profit","Margin %","Timestamp")

    """
    Method to update the table with new profit data. 
    It clears the existing data and populates the table with the latest profit information for each set, 
    including category, set name, component cost, sell price, tax, net profit, margin percentage, and timestamp. 
    The rows are color-coded based on whether the net profit exceeds a minimum profit margin.
    """
    def update_data(self, profits):
        """
        Known profits are sorted by net profit in descending order, and the 
        table is cleared before adding new rows to ensure the most profitable 
        sets are displayed at the top.
        """
        known = [p for p in profits if not p.missing_data]
        known.sort(key=lambda p: p.net_profit or 0, reverse=True)

        """
        Clear after sorting the known profits to ensure the table displays the most profitable sets at the top. 
        This is done before adding new rows to the table.
        """
        self.clear()

        for p in known:
            color = "green" if p.net_profit and p.net_profit > config.MIN_PROFIT_MARGIN else "red"
            self.add_row(
                p.category,
                p.set_name,
                f"{p.component_cost:,}" if p.component_cost is not None else "-",
                f"{p.set_sell_price:,}" if p.set_sell_price is not None else "-",
                f"{p.tax:,}" if p.tax is not None else "-",
                f"[{color}]{p.net_profit:,}[/{color}]" if p.net_profit is not None else "-",
                f"{p.margin_pct:.2f}%" if p.margin_pct is not None else "-",
                f"{format_seconds(p.age_total_set)}" if p.age_total_set is not None else "-",
            )

"""
Based on the SummaryTable class, the HighProfitTable class is defined to specifically display sets that meet a minimum profit margin.
Grabs the individual component prices and calculates the total cost of the set, the sell price of the set, the tax, and the net profit.
The HighProfitTable class inherits from DataTable and is used to display high-profit sets in a tabular format. It filters out sets that 
do not meet the minimum profit margin and sorts the remaining sets by net profit in descending order.
"""
class HighProfitTable(DataTable):
    """Component-level breakdown for sets over the profit threshold."""

    def on_mount(self) -> None:
        self.add_columns("Set", "Component", "Buy Price", "Age")

    def update_data(self, profits):
        known = [p for p in profits if not p.missing_data]
        high_profit = [
            p for p in known
            if p.net_profit is not None and p.net_profit > config.MIN_PROFIT_MARGIN
        ]
        high_profit.sort(key=lambda p: p.net_profit or 0, reverse=True)

        self.clear()
        for p in high_profit:
            for comp in p.components:
                self.add_row(
                    p.set_name,
                    comp.name,
                    f"{comp.buy_price:,}" if comp.buy_price is not None else "-",
                    format_seconds(comp.age_seconds),
                )

