import math
import time
import config   
from dataclasses import dataclass


def ge_tax (sell_price: int) -> int:
    """Calculate the Grand Exchange tax for a given price."""
    if sell_price < config.GE_TAX_NO_TAX_THRESHOLD:
        return 0
    tax = math.floor(sell_price * config.GE_TAX_RATE)
    return min(tax, config.GE_TAX_CAP)  # Tax is capped at the specified limit


# Container used to represent one component set and its components, along with the total buy price of the set.
@dataclass
class ComponentPrice:
    name: str # Item name Ex. "Blood Moon Chestplate"
    item_id: int # component name -> item ID
    buy_price: int | None # buy price (sell) from the API, or None if not available
    price_timestamp: int | None # timestamp of the price data, or None if not available

    # Property used to calculate the age of the price data for an individual component, returning the age in seconds or None if not available. This is useful for determining if the data is too old to be reliable.
    @property
    def age_seconds(self) -> int | None:
        """Return the age of the price data in seconds, or None if not available."""
        if self.price_timestamp is None:
            return None
        return int(time.time()) - self.price_timestamp

    # Property used to determine if the price data is stale based on the configured staleness threshold based on an individual component's price data. This is useful for determining if the data is too old to be reliable.
    @property 
    def is_stale(self) -> bool:
        """Return True if the price data is stale, False otherwise."""
        age = self.age_seconds
        return age is not None and age > config.STALENESS_THRESHOLD_SECONDS

# SetProfit represents the profit calculation for a given set and its components, including the total cost of components, the sell price of the set, the tax, and the net profit. It also includes flags for missing data and stale price data.
@dataclass
class SetProfit:
    category: str # Group name Ex. "Moons of Peril"
    set_name: str # Set name Ex. "Blood Moon Set"
    set_id: int  # id number from OSRS API for the set itself
    components: list[ComponentPrice] # List of components in the set, each with its name, ID, and buy price
    component_cost: int | None # Total cost of all components, or None if any component's price is missing
    set_sell_price: int | None # Sell price of the set itself, or None if not available
    set_price_time: int | None # Item ID of the set itself, or None if not available
    tax: int | None # Grand Exchange tax for the set
    net_profit: int | None # Net profit after accounting for tax
    margin_pct: float | None # Profit margin as a percentage
    missing_data: bool # True if any component or the set itself is missing price data, False otherwise

    @property 
    def age_total_set(self) -> int | None:
        """Gets the age of the set's price data, or None if not available."""
        if self.set_price_time is None:
            return None
        return (int(time.time()) - self.set_price_time)

    @property
    def component_ages(self) -> dict[str, int | None]:
        """Each component's individual age in seconds, keyed by name."""
        return {comp.name: comp.age_seconds for comp in self.components}

    @property
    def is_stale(self) -> bool:
        """Return True if any price data is stale, False otherwise."""
        return any(comp.is_stale for comp in self.components)


class SetProfitCalculator:
    """Calculates the profit for a given set and its components."""
    
    def __init__(self, client):
        self.client = client # OSRSPriceClient instance used to fetch live prices from the API

    def calculate_one_set(self, category, set_name, set_info, prices) -> SetProfit: 
        """
        Models the patient "margin flip" strategy: buy components at their low
        (buy-offer) price, sell the finished set at its high (sell-offer) price.
        This is the theoretical max margin - it assumes both offers eventually
        fill, which isn't guaranteed. age_seconds/is_stale flag results built
        from old trade data, which is riskier to rely on.
        """
        set_id = set_info["id"]
        components = set_info["components"]

        component_prices = []
        component_cost = 0
        missing_data = False

        for comp_name, comp_id in components.items():
            info = prices.get(comp_id)
            buy_price = info.get("low") if info else None
            buy_timestamp = info.get("lowTime") if info else None
            if buy_price is None: 
                missing_data = True
            else:
                component_cost += buy_price
            component_prices.append(ComponentPrice(comp_name, comp_id, buy_price, buy_timestamp))

        set_info = prices.get(set_id)
        set_sell_price = set_info.get("high") if set_info else None
        set_sell_timestamp = set_info.get("highTime") if set_info else None
        if set_sell_price is None:
            missing_data = True

        tax = net_profit = margin_pct = None
        if not missing_data:
            tax = ge_tax(set_sell_price)
            net_profit = set_sell_price - tax - component_cost
            if component_cost > 0:
                margin_pct = (net_profit / component_cost) * 100

        return SetProfit(
            category=category,
            set_name=set_name,
            set_id=set_id,
            components=component_prices,
            component_cost=component_cost if not missing_data else None,
            set_sell_price=set_sell_price,
            set_price_time=set_sell_timestamp,
            tax=tax,
            net_profit=net_profit,
            margin_pct=margin_pct,
            missing_data=missing_data,
        )


    def calculate_all_sets(self, sets_data: dict) -> list[SetProfit]:
        """Calculate profit for all sets in the provided sets_data dictionary."""
        prices = self.client.get_latest_prices()
        results = []
        for category, sets in sets_data.items():
            for set_name, set_info in sets.items():
                result = self.calculate_one_set(category, set_name, set_info, prices)
                results.append(result)
        return results





      



