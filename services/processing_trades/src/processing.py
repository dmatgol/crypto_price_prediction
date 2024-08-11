from finance_data_structures.volume_bars import VolumeBars
from quixstreams import Application
from settings.config import settings


class Preprocessing:
    """Preprocessing utilities."""

    def __init__(
        self, broker_address: str, input_topic: str, output_topic: str
    ) -> None:
        """Initialize the preprocessing step."""
        self.broker_address = broker_address
        self.input_topic = input_topic
        self.output_topic = output_topic

    def run(self) -> None:
        """Create trade bars for the defined methods."""
        # TODO: add support for run with different methods.
        # Idea is to iterate over every method and create bars for each
        # Need to create validation for available methods.
        app = Application(
            broker_address=self.broker_address,
            consumer_group="trade_to_volume_bar",
            auto_offset_reset="earliest",
        )

        input_topic = app.topic(name=self.input_topic, value_serializer="json")
        output_topic = app.topic(
            name=self.output_topic, value_serializer="json"
        )

        # Create a streaming dataframe to apply transformations to incoming data
        sdf = app.dataframe(input_topic)

        with app.get_producer() as producer:
            volume_bars = VolumeBars(
                producer,
                output_topic,
                settings.volume_interval,
            )
            # Apply the process_trade function to each incoming message
            sdf = sdf.apply(
                lambda trade: volume_bars.process_trade(
                    trade,
                )
            )

        # Run the application
        app.run(sdf)


if __name__ == "__main__":
    preprocessing = Preprocessing(
        settings.kafka.kafka_broker_address,
        settings.kafka.kafka_input_topic,
        settings.kafka.kafka_output_topic,
    )
    preprocessing.run()
