from abc import abstractmethod
from collections import defaultdict
from typing import Any

from utils.logging_config import logger


class FinanceDataStructure:
    """Finance data structure base class."""

    def __init__(
        self,
        output_producer: Any,
        ouput_topic: Any,
    ) -> None:
        """Initialize generic financial data structure.

        Args:
        ----
        output_producer (Any): Kafka producer.
        ouput_topic (Any): Kafka topic.
        threshold_interval (float): Threshold to create a bar.

        """
        self.output_producer = output_producer
        self.output_topic = ouput_topic
        self.bars: defaultdict[Any, Any] = defaultdict(
            lambda: self.initialize_bar(None, None, None)
        )

    @abstractmethod
    def initialize_bar(
        self, price: float, timestamp: int, product_id: str
    ) -> dict:
        """Initialize the data structure."""
        pass

    @abstractmethod
    def process_trade(self, trade: dict) -> None:
        """Process the trade and update the data structure."""
        pass

    @abstractmethod
    def is_bar_complete(
        self, bar: dict[str, Any], trade: dict[str, Any]
    ) -> bool:
        """Check if the bar is complete."""
        pass

    def get_bar(self, product_id: str) -> dict[str, Any]:
        """Get the current bar for a given product."""
        return self.bars[product_id]

    def write_bar_to_topic(
        self,
        product_id: str,
        bar: dict,
    ) -> None:
        """Write the completed bar to the output topic."""
        logger.info(f"Volume bar for {product_id}: {bar}")
        message = self.output_topic.serialize(product_id, value=bar)
        self.output_producer.produce(
            self.output_topic.name, value=message.value, key=message.key
        )
