import json 

from textual import work 
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, TabbedContent, TabPane 

import config 
from api import OSRSPriceClient
from calculate_sets import SetProfitCalculator
from widgets import SummaryTable, HighProfitTable

class OSRSPriceApp(App):
    """Main application class for the OSRS Price App."""

    """ CSS styling for the application, including layout and appearance of the header, footer, and tabbed content. """
    CSS = """ 
    TabbedContent ContentSwitcher {
    
        height: 1fr;
    }
    """
    def __init__(self): 
        super().__init__()
        self.sets_data = json.loads(config.ITEMS_SETS_FILE.read_text())
        self.client = OSRSPriceClient()
        self.calculator = SetProfitCalculator(self.client)

    def compose(self) -> ComposeResult:
        """Compose the main layout of the application, including the header, footer, and tabbed content with summary and high-profit tables."""
        yield Header()
        with TabbedContent():
            with TabPane("Summary", id="summary"):
                yield SummaryTable(id="summary_table")
            with TabPane("High Profit", id="high_profit"):
                yield HighProfitTable(id="high_profit_table")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the application is mounted. Starts the background task to refresh prices."""
        self.refresh_prices()  # Initial refresh on startup
        self.set_interval(config.REFRESH_INTERVAL_SECONDS, self.refresh_prices)  # Schedule periodic refreshes

    @work(thread=True, exclusive=True)
    def refresh_prices(self) -> None:
        """Fetches the latest prices and updates the tables. This method is run in a background thread to avoid blocking the UI."""
        try:
            profits = self.calculator.calculate_all_sets(self.sets_data)
        except Exception as e:
            self.call_from_thread(self.notify, f"Error fetching prices: {e}", severity="error")
            return
        self.call_from_thread(self.update_widgets, profits)

    def update_widgets(self, profits) -> None:
        """Updates the summary and high-profit tables with the latest profit data."""
        self.query_one(SummaryTable).update_data(profits)
        self.query_one(HighProfitTable).update_data(profits)