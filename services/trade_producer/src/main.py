import asyncio
from typing import Any

from api.coinbase import CoinBaseWebsocketTradeAPI
from api.kraken_api import KrakenWebsocketTradeAPI
from quixstreams import Application
from utils.logging_config import logger

from utils.helpers import get_configuration_parameters  # isort:skip
from utils.helpers import instanteate_websocket_apis  # isort:skip


def log_configuration_parameters(config: dict[str, Any]) -> None:
    """Log the configuration parameters.

    Args:
    ----
    config: The configuration parameters.

    """
    for key, value in config.items():
        logger.info(f"{key}: {value}")

    logger.info("Configuration parameters logged.")


async def produce_trades(config: dict[str, str]) -> None:
    """Read trades from Kraken websocket and send them to a Kafka topic.

    Args:
    ----
    config: The configuration parameters.

    """
    app = Application(broker_address=config["kafka_broker_address"])
    topic = app.topic(name=config["kafka_topic"], value_serializer="json")

    kraken_apis, coinbase_apis = instanteate_websocket_apis(config)

    # Producer write to kafka - send message to Kafka topic
    tasks = [
        run_websocket(api, app, topic) for api in kraken_apis + coinbase_apis
    ]

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
    config = get_configuration_parameters()
    log_configuration_parameters(config=config)
    asyncio.run(produce_trades(config))
