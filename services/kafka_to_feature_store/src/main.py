import json

from quixstreams import Application
from utils.logging_config import logger


def kafka_to_feature_store(
    kafka_broker_address: str,
    kafka_input_topic: str,
    feature_group_name: str,
    feature_group_version: int,
) -> None:
    """Read ohlc data from kafka and writes to feature store.

    Specifically, it write the data to the feature group specified by
    `feature_group_name` and `feature_group_version`.

    Args:
    ----
    kafka_broker_address (str): The kafka broker address.
    kafka_input_topic (str): The kafka topic to read from.
    feature_group_name (str): The name of the feature group to write to.
    feature_group_version (int): The version of the feature group to write to.

    """
    app = Application(
        broker_address=kafka_broker_address,
        consumer_group="kafka_to_feature_store",
    )

    with app.get_consumer() as consumer:
        consumer.subscribe(topics=[kafka_input_topic])

        while True:
            msg = consumer.poll(1)

            if msg is None:
                continue
            elif msg.error():
                logger.error("Kafka error:", format(msg.error()))
            else:
                json.loads(msg.value().decode("utf-8"))

            msg.value()

            consumer.store_offsets(message=msg)
