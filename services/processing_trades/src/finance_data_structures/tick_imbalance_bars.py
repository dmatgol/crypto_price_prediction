from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from quixstreams import State

from finance_data_structures.base import FinanceDataStructure
from settings.config import PRODUCT_ID_MAPPING, ProductId


@dataclass
class TradeSequence:
    """Helper class to track trade sequences within a bar."""

    side: str
    count: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert TradeSequence to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TradeSequence":
        """Create TradeSequence from dictionary."""
        return cls(**data)


class TickImbalanceBars(FinanceDataStructure):
    """Enhanced tick imbalance bars data structure with additional features."""

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
        """Initialize the data structure with additional features."""
        return {
            "product_id": product_id,
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "volume": 0,
            "start_time": timestamp,
            "end_time": timestamp,
            "tick_imbalance": 0,
            "ticks": 0,
            "cumulative_trade_amount": 0,
            # New features
            "net_buy_ratio": 0.0,
            "bar_formation_time": 0.0,
            "trade_intensity": 0.0,
            "max_buy_run": 0,
            "max_sell_run": 0,
            "price_volatility": 0.0,
            "price_path": [],  # To track price changes for volatility
            "trade_sequence": [],  # To track consecutive trades
        }

    def calculate_features(
        self,
        state: State,
        current_time: int,
        prices: list[float],
        trade_sequences: list[
            dict[str, Any]
        ],  # Now expects serialized sequences
    ) -> dict:
        """Calculate additional bar features."""
        buy_trades = state.get("buy_trades", default=0)
        total_ticks = state.get("ticks_counter", default=0)
        start_time = state.get("start_time", default=current_time)

        # 1. Net Buy Ratio (-1 to 1)
        net_buy_ratio = (
            (2 * (buy_trades / total_ticks) - 1) if total_ticks > 0 else 0
        )

        # 2. Bar Formation Time (seconds)
        bar_formation_time = (
            current_time - start_time
        ) / 1000  # Convert to seconds

        # 3. Intrabar Trade Intensity (trades per second)
        trade_intensity = (
            (total_ticks / bar_formation_time) if bar_formation_time > 0 else 0
        )

        # 4. Max Consecutive Buy/Sell Runs
        max_buy_run = 0
        max_sell_run = 0
        current_run = 0

        for seq in trade_sequences:
            if seq["side"] == "buy":
                if current_run > 0:
                    current_run += seq["count"]
                else:
                    current_run = seq["count"]
                max_buy_run = max(max_buy_run, current_run)
            else:  # sell
                if current_run < 0:
                    current_run -= seq["count"]
                else:
                    current_run = -seq["count"]
                max_sell_run = max(max_sell_run, abs(current_run))

        # 5. Intrabar Price Volatility
        # Using standard deviation of price changes
        price_volatility = np.std(prices) if len(prices) > 1 else 0

        return {
            "net_buy_ratio": round(net_buy_ratio, 4),
            "bar_formation_time": round(bar_formation_time, 4),
            "trade_intensity": round(trade_intensity, 4),
            "max_buy_run": max_buy_run,
            "max_sell_run": max_sell_run,
            "price_volatility": round(price_volatility, 4),
        }

    def process_trade(
        self, trade: dict[str, Any], state: State
    ) -> dict[str, Any]:
        """Create a new tick imbalance bar with enhanced features."""
        product_id = PRODUCT_ID_MAPPING.get(trade["product_id"])
        cumulative_imbalance = state.get("cumulative_imbalance", default=0)
        buy_trades = state.get("buy_trades", default=0)
        ticks_counter = state.get("ticks_counter", default=0)
        high = state.get("high", default=0)
        low = state.get("low", default=99999999999)
        volume = state.get("volume", default=0)
        cumulative_trade_amount = state.get(
            "cumulative_trade_amount", default=0
        )

        # Get or initialize price path and trade sequence lists
        price_path = state.get("price_path", default=[])
        trade_sequences_data = state.get("trade_sequences", default=[])
        trade_sequences = [
            TradeSequence.from_dict(seq) for seq in trade_sequences_data
        ]

        # Update price path
        price_path.append(trade["price"])
        state.set("price_path", price_path)

        # Update trade sequences for tracking consecutive trades
        if trade_sequences and trade_sequences[-1].side == trade["side"]:
            trade_sequences[-1].count += 1
        else:
            trade_sequences.append(TradeSequence(side=trade["side"]))

        # Serialize trade sequences before storing in state
        state.set("trade_sequences", [seq.to_dict() for seq in trade_sequences])

        if trade["side"] == "buy":
            cumulative_imbalance += 1
            buy_trades += 1
            state.set("buy_trades", buy_trades)
            state.set("cumulative_imbalance", cumulative_imbalance)
        elif trade["side"] == "sell":
            cumulative_imbalance -= 1
            state.set("cumulative_imbalance", cumulative_imbalance)
        else:
            raise ValueError(f"Invalid trade side: {trade['side']}")

        if abs(cumulative_imbalance) >= self.threshold_intervals[product_id]:
            bar = self.get_bar(product_id)

            # Calculate additional features
            additional_features = self.calculate_features(
                state,
                trade["timestamp"],
                price_path,
                [
                    seq.to_dict() for seq in trade_sequences
                ],  # Convert to list of dicts
            )

            bar.update(
                {
                    "product_id": product_id,
                    "open": state.get("open"),
                    "high": max(high, trade["price"]),
                    "low": min(low, trade["price"]),
                    "close": trade["price"],
                    "volume": round(volume + trade["volume"], 4),
                    "end_time": trade["timestamp"],
                    "start_time": state.get("start_time"),
                    "tick_imbalance": cumulative_imbalance,
                    "ticks": state.get("ticks_counter"),
                    "cumulative_trade_amount": round(
                        cumulative_trade_amount
                        + trade["volume"] * trade["price"],
                        4,
                    ),
                    **additional_features,  # Add the new features
                }
            )

            self.write_bar_to_topic(product_id, bar)

            # Reset state
            state.set("product_id", None)
            state.set("cumulative_imbalance", 0)
            state.set("ticks_counter", 0)
            state.set("buy_trades", 0)
            state.set("high", 0)
            state.set("low", 99999999999)
            state.set("volume", 0)
            state.set("cumulative_trade_amount", 0)
            state.set("price_path", [])
            state.set("trade_sequences", [])
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
            state.set(
                "cumulative_trade_amount",
                cumulative_trade_amount + trade["volume"] * trade["price"],
            )

        return trade
