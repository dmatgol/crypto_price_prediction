from typing import Any

from finance_data_structures.base import FinanceDataStructure


class VolumeBars(FinanceDataStructure):
    """Volume bars data structure."""

    def initialize_bar(self, price: float, timestamp: int) -> dict[str, Any]:
        """Initialize the data structure."""
        return {
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
        product_id = trade["product_id"]
        price = trade["price"]
        volume = trade["volume"]
        timestamp = trade["timestamp"]

        while volume > 0:
            bar = self.get_bar(product_id)

            if bar["open"] is None:
                bar.update(self.initialize_bar(price, timestamp))

            bar["high"] = max(bar["high"], price)
            bar["low"] = min(bar["low"], price)
            bar["close"] = price
            bar["end_time"] = timestamp

            remaining_volume = self.threshold_interval - bar["volume"]

            if self.is_bar_complete(volume, remaining_volume):
                bar["volume"] = self.threshold_interval
                volume -= remaining_volume
                self.write_bar_to_topic(product_id, bar)
                self.bars[product_id] = self.initialize_bar(price, timestamp)
            else:
                bar["volume"] += volume
                volume = 0
        return trade

    def is_bar_complete(self, volume: float, remaining_volume: float) -> bool:
        """Verify if new trade completes volume bar."""
        return volume >= remaining_volume
