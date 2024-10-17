from typing import Any

from finance_data_structures.base import FinanceDataStructure
from quixstreams import State
from settings.config import PRODUCT_ID_MAPPING, ProductId


class TickImbalanceBars(FinanceDataStructure):
    """Tick imbalance bars data structure."""

    def __init__(
        self, output_producer: Any, output_topic: Any, products: list[ProductId]
    ) -> None:
        """Initialize the tick imbalance-based financial data structure."""
        super().__init__(output_producer, output_topic)
        self.threshold_intervals = {
            PRODUCT_ID_MAPPING.get(product.coin): product.aggregation.interval
            for product in products
        }

    def initialize_bar(
        self, price: float, timestamp: int, product_id: str
    ) -> dict:
        """Initialize the data structure."""
        return {
            "product_id": product_id,
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "volume": 0,
            "start_time": timestamp,
            "end_time": timestamp,
        }

    def process_trade(
        self, trade: dict[str, Any], state: State
    ) -> dict[str, Any]:
        """Create a new tick imbalance bar at every X trade volume.

        Args:
        ----
        trade (dict[str, Any]): trade object.
        state (State): State object to keep track of cumulative trade numbers.

        """
        product_id = PRODUCT_ID_MAPPING.get(trade["product_id"])
        cumulative_imbalance = state.get("cumulative_imbalance", default=0)
        ticks_counter = state.get("ticks_counter", default=0)
        high = state.get("high", default=0)
        low = state.get("low", default=99999999999)
        volume = state.get("volume", default=0)

        if trade["side"] == "buy":
            cumulative_imbalance += 1
            state.set("cumulative_imbalance", cumulative_imbalance)
        elif trade["side"] == "sell":
            cumulative_imbalance -= 1
            state.set("cumulative_imbalance", cumulative_imbalance)
        else:
            raise ValueError(f"Invalid trade side: {trade['side']}")

        if abs(cumulative_imbalance) > self.threshold_intervals[product_id]:
            bar = self.get_bar(product_id)
            bar.update(
                {
                    "product_id": product_id,
                    "open": state.get("open"),
                    "high": max(high, trade["price"]),
                    "low": min(low, trade["price"]),
                    "close": trade["price"],
                    "volume": volume + trade["volume"],
                    "end_time": trade["timestamp"],
                    "start_time": state.get("start_time"),
                    "tick_imbalance": cumulative_imbalance,
                }
            )
            self.write_bar_to_topic(product_id, bar)
            # Reset state
            state.set("product_id", None)
            state.set("cumulative_imbalance", 0)
            state.set("ticks_counter", 0)
            state.set("high", 0)
            state.set("low", 99999999999)
            state.set("volume", 0)
            self.bars[product_id] = self.initialize_bar(None, None, None)

        else:
            ticks_counter += 1
            state.set("ticks_counter", ticks_counter)
            if ticks_counter == 1:
                state.set("start_time", trade["timestamp"])
                state.set("open", trade["price"])
            state.set("high", max(high, trade["price"]))
            state.set("low", min(low, trade["price"]))
            state.set("volume", volume + trade["volume"])

        return trade
