from quixstreams import Application
from settings.config import settings
from utils.logging_config import logger


def trades_to_volume_bars(
    kafka_input_topic: str,
    kafka_output_topic: str,
    kafka_broker_address: str,
    volume_interval: int,
) -> None:
    """Create volme bars.

    Read trades from the kafka input topic.
    Aggregate the data into volume bars using the specified volume interval.
    Save the volume bars into another topic.

    Args:
    ----
    kafka_input_topic (str): Kafka topic to read data from.
    kafka_output_topic (str): Kafka topic to write data to.
    kafka_broker_address (str): Kafka address
    volume_interval (int): Volume of trades to create a volume bar.

    """
    app = Application(
        broker_address=kafka_broker_address,
        consumer_group="trade_to_volume_bar",
    )
    input_topic = app.topic(name=kafka_input_topic, value_serializer="json")
    app.topic(name=kafka_output_topic, value_serializer="json")

    # Create a streaming dataframe to apply transformations to incoming data
    sdf = app.dataframe(input_topic)

    # Apply transformations
    # TODO

    app.run(sdf)


if __name__ == "__main__":
    logger.info(f"{settings}")
    trades_to_volume_bars(
        kafka_input_topic=settings.kafka.kafka_input_topic,
        kafka_output_topic=settings.kafka.kafka_output_topic,
        kafka_broker_address=settings.kafka.kafka_broker_address,
        volume_interval=settings.volume_interval,
    )
