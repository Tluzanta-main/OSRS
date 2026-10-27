import pytest

import calculate_sets
from calculate_sets import SetProfitCalculator, ge_tax

NOW = 1_700_000_000  # fixed fake clock, in Unix seconds

# One set with two components, shaped like an entry in items_sets.json.
SET_INFO = {"id": 900, "components": {"Helm": 1, "Body": 2}}


class FakeClient:
    """Stands in for OSRSPriceClient: returns canned prices, counts calls."""

    def __init__(self, prices):
        self.prices = prices
        self.calls = 0

    def get_latest_prices(self):
        self.calls += 1
        return self.prices


def price(high=None, low=None, high_time=None, low_time=None):
    """One item's entry, shaped like the API's /latest data."""
    return {"high": high, "highTime": high_time, "low": low, "lowTime": low_time}


def calc_one(prices, set_info=SET_INFO):
    calc = SetProfitCalculator(FakeClient(prices))
    return calc.calculate_one_set("Test", "Test set", set_info, prices)


# --- ge_tax ---

@pytest.mark.parametrize("sell_price, expected", [
    (0, 0),
    (49, 0),   # last untaxed price
    (50, 1),   # first taxed price: 50 * 0.02 = 1
])
def test_tax_is_zero_below_threshold(sell_price, expected):
    assert ge_tax(sell_price) == expected


@pytest.mark.parametrize("sell_price, expected", [
    (149, 2),     # 149 * 0.02 = 2.98 -> 2
    (1_049, 20),  # 1,049 * 0.02 = 20.98 -> 20
])
def test_tax_rounds_down(sell_price, expected):
    assert ge_tax(sell_price) == expected


@pytest.mark.parametrize("sell_price, expected", [
    (249_999_999, 4_999_999),      # 4,999,999.98 -> 4,999,999, just under cap
    (250_000_000, 5_000_000),      # exactly the cap
    (1_000_000_000, 5_000_000),    # 20,000,000 capped to 5,000,000
])
def test_tax_is_capped(sell_price, expected):
    assert ge_tax(sell_price) == expected


# --- calculate_one_set ---

def test_profitable_set_math():
    prices = {
        1: price(low=1_000_000),
        2: price(low=2_000_000),
        900: price(high=3_200_000),
    }
    result = calc_one(prices)
    assert result.missing_data is False
    assert result.component_cost == 3_000_000        # 1,000,000 + 2,000,000
    assert result.set_sell_price == 3_200_000
    assert result.tax == 64_000                      # 3,200,000 * 0.02
    assert result.net_profit == 136_000              # 3,200,000 - 64,000 - 3,000,000
    assert result.margin_pct == pytest.approx(4.5333333)  # 136,000 / 3,000,000 * 100


def test_losing_set_has_negative_profit_and_margin():
    prices = {
        1: price(low=1_000_000),
        2: price(low=2_000_000),
        900: price(high=3_000_000),
    }
    result = calc_one(prices)
    assert result.tax == 60_000              # 3,000,000 * 0.02
    assert result.net_profit == -60_000      # 3,000,000 - 60,000 - 3,000,000
    assert result.margin_pct == pytest.approx(-2.0)  # -60,000 / 3,000,000 * 100


@pytest.mark.parametrize("prices", [
    # component 2 not in the API data at all
    {1: price(low=1_000_000), 900: price(high=3_200_000)},
    # the set itself not in the API data
    {1: price(low=1_000_000), 2: price(low=2_000_000)},
    # component 2 present, but its low price is null
    {1: price(low=1_000_000), 2: price(low=None), 900: price(high=3_200_000)},
], ids=["component-absent", "set-absent", "component-low-null"])
def test_missing_price_marks_set_missing(prices):
    result = calc_one(prices)
    assert result.missing_data is True
    assert result.component_cost is None
    assert result.tax is None
    assert result.net_profit is None
    assert result.margin_pct is None


# --- ages and staleness (fake clock) ---

@pytest.fixture
def fixed_clock(monkeypatch):
    monkeypatch.setattr(calculate_sets.time, "time", lambda: NOW)
    monkeypatch.setattr(calculate_sets.config, "STALENESS_THRESHOLD_SECONDS", 3600)


def test_component_at_threshold_is_not_stale(fixed_clock):
    prices = {
        1: price(low=1_000_000, low_time=NOW - 3600),
        2: price(low=2_000_000, low_time=NOW - 3600),
        900: price(high=3_200_000, high_time=NOW - 120),
    }
    result = calc_one(prices)
    assert result.components[0].age_seconds == 3600
    assert result.components[0].is_stale is False
    assert result.is_stale is False
    assert result.age_total_set == 120


def test_component_just_past_threshold_makes_set_stale(fixed_clock):
    prices = {
        1: price(low=1_000_000, low_time=NOW - 3600),
        2: price(low=2_000_000, low_time=NOW - 3601),
        900: price(high=3_200_000, high_time=NOW - 120),
    }
    result = calc_one(prices)
    assert result.components[1].is_stale is True
    assert result.is_stale is True
    assert result.component_ages == {"Helm": 3600, "Body": 3601}


# --- calculate_all_sets ---

def test_calculate_all_sets_fetches_once_and_returns_every_set_in_order():
    sets_data = {
        "Cat A": {
            "Set 1": {"id": 900, "components": {"Helm": 1}},
            "Set 2": {"id": 901, "components": {"Body": 2}},
        },
        "Cat B": {
            "Set 3": {"id": 902, "components": {"Legs": 3}},
        },
    }
    client = FakeClient({})
    results = SetProfitCalculator(client).calculate_all_sets(sets_data)
    assert client.calls == 1
    assert [(r.category, r.set_name) for r in results] == [
        ("Cat A", "Set 1"),
        ("Cat A", "Set 2"),
        ("Cat B", "Set 3"),
    ]
