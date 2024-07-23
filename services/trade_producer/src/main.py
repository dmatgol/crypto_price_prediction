from typing import Any

from api.kraken_api import KrakenWebsocketTradeAPI
from quixstreams import Application
from utils.config import config, logger


def log_configuration_parameters(config: dict[str, Any]) -> None:
    """Log the configuration parameters.

    Args:
    ----
    config: The configuration parameters.

    """
    for key, value in config.items():
        logger.info(f"{key}: {value}")

    logger.info("Configuration parameters logged.")


def produce_trades(
    kakfka_broker_address: str, kafka_topic: str, product_ids: list[str]
) -> None:
    """Read trades from Kraken websocket and send them to a Kafka topic.

    Args:
    ----
    kakfka_broker_address: The address of Kafka broker.
    kafka_topic: The name of the Kafka topic.
    product_ids: The product IDs to subscribe to.

    """
    app = Application(broker_address=kakfka_broker_address)
    topic = app.topic(name=kafka_topic, value_serializer="json")

    kraken_api = KrakenWebsocketTradeAPI(product_ids=product_ids)
    # Producer write to kafka - send message to Kafka topic
    with app.get_producer() as producer:

        while True:

            trades: list[dict] = kraken_api.get_trades()
            for trade in trades:
                logger.info(trade)
                message = topic.serialize(trade["product_id"], value=trade)

                # Produce a message into the topic
                producer.produce(
                    topic=topic.name, value=message.value, key=message.key
                )


if __name__ == "__main__":

    log_configuration_parameters(config=config)
    produce_trades(
        kakfka_broker_address=config["kafka"]["kakfka_broker_address"],
        kafka_topic=config["kafka"]["kafka_topic"],
        product_ids=config["instrument"]["product_ids"],
    )
