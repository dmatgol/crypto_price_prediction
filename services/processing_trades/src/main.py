from collections import defaultdict
from typing import Any

from quixstreams import Application
from settings.config import settings
from utils.logging_config import logger


def initialize_volume_bar(price: float, timestamp: int) -> dict:
    """Initialize a new volume bar with the given price and timestamp."""
    return {
        "open": price,
        "high": price,
        "low": price,
        "close": price,
        "volume": 0,
        "start_time": timestamp,
        "end_time": timestamp,
    }


def output_volume_bar(producer, topic: Any, product_id: str, bar: dict) -> None:
    """Send the completed volume bar to the output topic."""
    logger.info(f"Volume bar for {product_id}: {bar}")
    message = topic.serialize(product_id, value=bar)
    producer.produce(topic.name, value=message.value, key=message.key)


def process_trade(
    trade: dict,
    volume_bars: defaultdict,
    volume_interval: int,
    output_producer: Any,
    kafka_output_topic: Any,
) -> dict:
    """Process each trade and accumulate it into volume bars."""
    product_id = trade["product_id"]
    price = trade["price"]
    volume = trade["volume"]
    timestamp = trade["timestamp"]

    while volume > 0:
        bar = volume_bars[product_id]

        if bar["open"] is None:
            bar.update(initialize_volume_bar(price, timestamp))

        bar["high"] = max(bar["high"], price)
        bar["low"] = min(bar["low"], price)
        bar["close"] = price
        bar["end_time"] = timestamp

        remaining_volume = volume_interval - bar["volume"]

        if volume >= remaining_volume:
            bar["volume"] = volume_interval
            volume -= remaining_volume
            output_volume_bar(
                output_producer, kafka_output_topic, product_id, bar
            )
            volume_bars[product_id] = initialize_volume_bar(
                price, timestamp
            )  # Start new bar
        else:
            bar["volume"] += volume
            volume = 0

    return trade  # Returning the trade to continue in the pipeline


def trades_to_volume_bars(
    kafka_input_topic: str,
    kafka_output_topic: str,
    kafka_broker_address: str,
    volume_interval: int,
) -> None:
    """Create volume bars from trades."""
    app = Application(
        broker_address=kafka_broker_address,
        consumer_group="trade_to_volume_bar",
        auto_offset_reset="earliest",
    )
    input_topic = app.topic(name=kafka_input_topic, value_serializer="json")
    output_topic = app.topic(name=kafka_output_topic, value_serializer="json")

    # Initialize the volume bars storage
    volume_bars: defaultdict[Any, Any] = defaultdict(
        lambda: initialize_volume_bar(None, None)
    )

    # Create a streaming dataframe to apply transformations to incoming data
    sdf = app.dataframe(input_topic)

    with app.get_producer() as producer:
        # Apply the process_trade function to each incoming message
        sdf = sdf.apply(
            lambda trade: process_trade(
                trade,
                volume_bars,
                volume_interval,
                producer,
                output_topic,
            )
        )

    # Run the application
    app.run(sdf)


if __name__ == "__main__":
    logger.info(f"{settings}")
    trades_to_volume_bars(
        kafka_input_topic=settings.kafka.kafka_input_topic,
        kafka_output_topic=settings.kafka.kafka_output_topic,
        kafka_broker_address=settings.kafka.kafka_broker_address,
        volume_interval=settings.volume_interval,
    )
