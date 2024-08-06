import asyncio
import time
from typing import Any

from api.coinbase import CoinBaseWebsocketTradeAPI
from api.kraken_api import KrakenWebsocketTradeAPI
from monitoring.monitoring_metrics import monitoring
from quixstreams import Application
from settings.config import settings
from utils.logging_config import logger

from utils.helpers import instanteate_websocket_apis  # isort:skip


async def produce_trades() -> None:
    """Read trades from Kraken websocket and send them to a Kafka topic.

    Args:
    ----
    config: The configuration parameters.

    """
    app = Application(broker_address=settings.kafka.kafka_broker_address)
    topic = app.topic(name=settings.kafka.kafka_topic, value_serializer="json")

    kraken_apis, coinbase_apis = instanteate_websocket_apis()

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
                # Monitor performance
                start_time = time.time()
                trades = await websocket_api.run()
                latency = time.time() - start_time
                monitoring.observe_request(
                    exchange=websocket_api.name, metric=latency
                )
                monitoring.increment_request_count(exchange=websocket_api.name)

                # Send trades to redpanda
                for trade in trades:
                    logger.info(trade)
                    message = topic.serialize(trade["product_id"], value=trade)
                    producer.produce(
                        topic.name, value=message.value, key=message.key
                    )


if __name__ == "__main__":
    logger.info(f"{settings}")
    logger.info("Configuration parameters logged.")
    asyncio.run(produce_trades())
