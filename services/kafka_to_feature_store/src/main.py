import json

from hopswork.hopswork_api import push_data_to_feature_store
from quixstreams import Application
from settings.config import settings
from utils.logging_config import logger


class PublishToFeatureStore:
    """Publish features to feature store."""

    def __init__(self, broker_address: str, input_topic: str) -> None:
        """Initialize the consumer step.

        Args:
        ----
        broker_address (str): The kafka broker address.
        input_topic (str): The kafka topic to read from.

        """
        self.broker_address = broker_address
        self.input_topic = input_topic

    def run(self) -> None:
        """Read ohlc data from kafka and writes to feature store.

        Specifically, it write the data to the feature group specified by
        `feature_group_name` and `feature_group_version`.
        """
        app = Application(
            broker_address=self.broker_address,
            consumer_group="kafka_to_hopswork_feature_store",
            auto_offset_reset="earliest",
        )
        input_topic = app.topic(name=self.input_topic, value_serializer="json")

        with app.get_consumer() as consumer:
            consumer.subscribe(topics=[input_topic.name])

            while True:
                msg = consumer.poll(1)

                if msg is None:
                    continue
                elif msg.error():
                    logger.error("Kafka error:", format(msg.error()))
                else:
                    ohlc_message = json.loads(msg.value().decode("utf-8"))
                    push_data_to_feature_store(
                        feature_group_name="ohlc_feature_group",
                        feature_group_version=1,
                        data=ohlc_message,
                    )

                    consumer.store_offsets(message=ohlc_message)


if __name__ == "__main__":
    write_to_feature_store = PublishToFeatureStore(
        settings.kafka.broker_address,
        settings.kafka.input_topic,
    )
    write_to_feature_store.run()
