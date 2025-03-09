import json
import uuid
from datetime import datetime, timezone

from hopswork.hopswork_api import push_data_to_feature_store
from quixstreams import Application
from settings.config import settings
from utils.logging_config import logger


def get_current_utc_sec() -> int:
    """Return the current UTC time expressed in seconds since the epoch."""
    return int(datetime.now(timezone.utc).timestamp())


class PublishToFeatureStore:
    """Publish features to feature store."""

    def __init__(
        self,
        broker_address: str,
        input_topic: str,
        feature_group_primary_keys: list[str],
        feature_group_event_time: str,
        consumer_group: str | None,
        new_consumer_group: bool,
        feature_group: str | None,
        feature_group_version: int | None,
        buffer_size: int | None = 1,
        live_or_historical: str | None = "live",
        save_every_n_sec: int | None = 600,
    ) -> None:
        """Initialize the consumer step.

        Args:
        ----
        broker_address (str): The kafka broker address.
        input_topic (str): The kafka topic to read from.
        buffer_size (int, optional): The buffer size. Defaults to 1000.
        consumer_group (str): The Kafka consumer group to read messages.
        new_consumer_group (bool): Whether to create a new consumer group.
        feature_group (str): The name of the feature group to write to.
        feature_group_version (int): Feature group version to write to.
        feature_group_primary_keys (List[str]): The PR of the Feature Group
        feature_group_event_time (str): The event time of the Feature Group
        live_or_historical (str, optional): Whether we are saving live data to
            the Feature or historical data.
            Live data goes to the online feature store
            While historical data goes to the offline feature store.
        save_every_n_sec (int, optional): The max seconds to wait before
            writing the data to the feature store.

        """
        self.broker_address = broker_address
        self.input_topic = input_topic
        self.consumer_group = consumer_group
        self.new_consumer_group = new_consumer_group
        self.feature_group = feature_group
        self.feature_group_version = feature_group_version
        self.feature_group_primary_keys = feature_group_primary_keys
        self.feature_group_event_time = feature_group_event_time
        self.buffer_size = buffer_size
        self.live_or_historical = live_or_historical
        self.save_every_n_sec = save_every_n_sec

    def run(self) -> None:
        """Read ohlc data from kafka and writes to feature store.

        Specifically, it write the data to the feature group specified by
        `feature_group_name` and `feature_group_version`.
        """
        if self.new_consumer_group:
            self.consumer_group = f"{self.consumer_group}_{uuid.uuid4()}"
            logger.debug(f"New Consumer group: {self.consumer_group}")

        app = Application(
            broker_address=self.broker_address,
            consumer_group=self.consumer_group,
            auto_offset_reset="earliest",
        )

        input_topic = app.topic(name=self.input_topic, value_serializer="json")

        last_saved_to_feature_store_ts = get_current_utc_sec()

        buffer: list[dict] = []

        with app.get_consumer() as consumer:
            consumer.subscribe(topics=[input_topic.name])
            while True:
                msg = consumer.poll(1)
                sec_since_last_saved = (
                    get_current_utc_sec() - last_saved_to_feature_store_ts
                )

                if msg is None:
                    # If no message is received/ all messages are received
                    # then save the remaining buffer
                    if buffer and (
                        sec_since_last_saved >= self.save_every_n_sec
                    ):
                        push_data_to_feature_store(
                            self.feature_group,
                            self.feature_group_version,
                            self.feature_group_primary_keys,
                            self.feature_group_event_time,
                            buffer,
                            online_offline=(
                                "online"
                                if self.live_or_historical == "live"
                                else "offline"
                            ),
                        )
                        logger.info(
                            f"Buffer of {len(buffer)} messages sent to feature"
                            "store"
                        )
                        buffer = []
                        last_saved_to_feature_store_ts = get_current_utc_sec()
                    if not buffer and (
                        sec_since_last_saved >= self.save_every_n_sec
                    ):
                        logger.info("No messages received. Exiting.")
                        return
                else:
                    if msg.error():
                        logger.error("Kafka error:", format(msg.error()))

                    ohlc_message = json.loads(msg.value().decode("utf-8"))
                    buffer.append(ohlc_message)

                    if len(buffer) >= self.buffer_size:
                        push_data_to_feature_store(
                            self.feature_group,
                            self.feature_group_version,
                            self.feature_group_primary_keys,
                            self.feature_group_event_time,
                            buffer,
                            online_offline=(
                                "online"
                                if self.live_or_historical == "live"
                                else "offline"
                            ),
                        )
                        logger.info(
                            f"Buffer of {len(buffer)} messages sent to feature"
                            "store"
                        )
                        buffer = []
                        last_saved_to_feature_store_ts = get_current_utc_sec()

                    consumer.store_offsets(message=msg)


if __name__ == "__main__":
    logger.info(settings)
    write_to_feature_store = PublishToFeatureStore(
        settings.app_settings.kafka_broker_address,
        settings.app_settings.input_topic,
        settings.app_settings.feature_group_primary_keys,
        settings.app_settings.feature_group_event_time,
        settings.app_settings.consumer_group,
        settings.app_settings.create_new_consumer_group,
        settings.app_settings.feature_group,
        settings.app_settings.feature_group_version,
        settings.app_settings.buffer_size,
        settings.live_or_historical,
        settings.save_every_n_sec,
    )
    write_to_feature_store.run()
