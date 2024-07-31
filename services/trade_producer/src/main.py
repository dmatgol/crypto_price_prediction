import asyncio
from typing import Any

from api.coinbase import CoinBaseWebsocketTradeAPI
from api.kraken_api import KrakenWebsocketTradeAPI
from quixstreams import Application
from utils.helpers import instanteate_websocket_apis
from utils.logging_config import config, logger


def log_configuration_parameters(config: dict[str, Any]) -> None:
    """Log the configuration parameters.

    Args:
    ----
    config: The configuration parameters.

    """
    for key, value in config.items():
        logger.info(f"{key}: {value}")

    logger.info("Configuration parameters logged.")


async def produce_trades(
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

    kraken_apis, coinbase_apis = instanteate_websocket_apis()

    # Producer write to kafka - send message to Kafka topic
    tasks = []
    for kraken_api in kraken_apis:
        tasks.append(asyncio.create_task(run_websocket(kraken_api, app, topic)))
    for coinbase_api in coinbase_apis:
        tasks.append(
            asyncio.create_task(run_websocket(coinbase_api, app, topic))
        )

    await asyncio.gather(*tasks)


async def run_websocket(
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
    async with websocket_api:
        with app.get_producer() as producer:
            while True:
                trades = await websocket_api.run()
                for trade in trades:
                    logger.info(trade)
                    message = topic.serialize(trade["product_id"], value=trade)
                    producer.produce(
                        topic.name, value=message.value, key=message.key
                    )


if __name__ == "__main__":

    log_configuration_parameters(config=config)
    asyncio.run(
        produce_trades(
            kakfka_broker_address=config["kafka"]["kakfka_broker_address"],
            kafka_topic=config["kafka"]["kafka_topic"],
        )
    )
