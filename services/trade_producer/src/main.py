from typing import Any

from api.coinbase import CoinBaseWebsocketTradeAPI
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


def instanteate_websocket_apis() -> (
    tuple[KrakenWebsocketTradeAPI, CoinBaseWebsocketTradeAPI]
):
    """Instantiate KrakenWebsocketTradeAPI and CoinBaseWebsocketTradeAPI.

    Returns
    -------
    A tuple of KrakenWebsocketTradeAPI and CoinBaseWebsocketTradeAPI.

    """
    kraken_api = KrakenWebsocketTradeAPI(
        product_ids=config["exchanges"][0]["product_ids"],
        channels=config["exchanges"][0]["channels"],
    )
    coinbase_api = CoinBaseWebsocketTradeAPI(
        product_ids=config["exchanges"][1]["product_ids"],
        channels=config["exchanges"][1]["channels"],
    )
    return kraken_api, coinbase_api


def produce_trades(
    kakfka_broker_address: str,
    kafka_topic: str,
) -> None:
    """Read trades from Kraken websocket and send them to a Kafka topic.

    Args:
    ----
    kakfka_broker_address: The address of Kafka broker.
    kafka_topic: The name of the Kafka topic.

    """
    app = Application(broker_address=kakfka_broker_address)
    topic = app.topic(name=kafka_topic, value_serializer="json")

    kraken_api, coinbase_api = instanteate_websocket_apis()

    # Producer write to kafka - send message to Kafka topic
    # tasks = [
    #    asyncio.create_task(run_websocket(kraken_api, app, topic)),
    #    asyncio.create_task(run_websocket(coinbase_api, app, topic)),
    # ]

    run_websocket(coinbase_api, app, topic)

    # await asyncio.gather(*tasks)


def run_websocket(
    websocket_api: KrakenWebsocketTradeAPI | CoinBaseWebsocketTradeAPI,
    app: Application,
    topic: Any,
):
    """Run the websocket API.

    Args:
    ----
    websocket_api: The websocket API to run.
    app: The Quix application.
    topic: The Kafka topic.

    """
    with app.get_producer() as producer:
        while True:
            trades = websocket_api.run()
            for trade in trades:
                logger.info(trade)
                message = topic.serialize(trade["product_id"], value=trade)
                producer.produce(
                    topic.name, value=message.value, key=message.key
                )


if __name__ == "__main__":

    log_configuration_parameters(config=config)
    # asyncio.run(
    produce_trades(
        kakfka_broker_address=config["kafka"]["kakfka_broker_address"],
        kafka_topic=config["kafka"]["kafka_topic"],
    )
    # )
