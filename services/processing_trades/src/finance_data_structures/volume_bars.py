from typing import Any

from finance_data_structures.base import FinanceDataStructure
from settings.config import PRODUCT_ID_MAPPING, ProductId
from utils.twitter_snowflake import sf_id_generator


class VolumeBars(FinanceDataStructure):
    """Volume bars data structure."""

    def __init__(
        self, output_producer: Any, output_topic: Any, products: list[ProductId]
    ) -> None:
        """Initialize the volume-based financial data structure."""
        super().__init__(output_producer, output_topic)
        self.threshold_intervals = {
            PRODUCT_ID_MAPPING.get(product.coin): product.aggregation.interval
            for product in products
        }

    def initialize_bar(
        self, price: float, timestamp: int, product_id: str
    ) -> dict[str, Any]:
        """Initialize the data structure."""
        return {
            "unique_id": sf_id_generator.generate_id(),
            "product_id": product_id,
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "volume": 0,
            "start_time": timestamp,
            "end_time": timestamp,
        }

    def process_trade(self, trade: dict[str, Any]) -> dict[str, Any]:
        """Create a new volume bar at every X trade volume.

        Args:
        ----
        trade (dict[str, Any]): trade object.

        """
        product_id = PRODUCT_ID_MAPPING.get(trade["product_id"])
        price = trade["price"]
        volume = trade["volume"]
        timestamp = trade["timestamp"]

        while volume > 0:
            bar = self.get_bar(product_id)

            if bar["open"] is None:
                bar.update(self.initialize_bar(price, timestamp, product_id))

            bar["high"] = max(bar["high"], price)
            bar["low"] = min(bar["low"], price)
            bar["close"] = price
            bar["end_time"] = timestamp

            remaining_volume = (
                self.threshold_intervals[product_id] - bar["volume"]
            )

            if self.is_bar_complete(volume, remaining_volume):
                bar["volume"] = self.threshold_intervals[product_id]
                volume -= remaining_volume

                # Write bar to topic
                self.write_bar_to_topic(product_id, bar)
                self.bars[product_id] = self.initialize_bar(
                    price, timestamp, product_id
                )
            else:
                bar["volume"] += volume
                volume = 0
        return trade

    def is_bar_complete(self, volume: float, remaining_volume: float) -> bool:
        """Verify if new trade completes volume bar."""
        return volume >= remaining_volume
