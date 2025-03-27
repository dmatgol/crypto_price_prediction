import asyncio
import time
from typing import Any

from api.base_rest import BaseExchangeRestAPI
from api.base_websocket import BaseExchangeWebSocket
from monitoring.monitoring_metrics import monitoring
from quixstreams import Application
from settings.config import settings
from utils.logging_config import logger

from utils.helpers import instanteate_apis  # isort:skip


async def produce_trades() -> None:
    """Read trades from from api and send them to a Kafka topic.

    Supports both websocket and rest apis.

    Args:
    ----
    config: The configuration parameters.

    """
    app = Application(broker_address=settings.kafka.kafka_broker_address)
    topic = app.topic(name=settings.kafka.kafka_topic, value_serializer="json")

    kraken_apis, coinbase_apis = instanteate_apis()

    # Producer write to kafka - send message to Kafka topic
    tasks = [run_apis(api, app, topic) for api in kraken_apis + coinbase_apis]

    await asyncio.gather(*tasks)


async def run_apis(
    api: BaseExchangeWebSocket | BaseExchangeRestAPI,
    app: Application,
    topic: Any,
):
    """Run the websocket API.

    Args:
    ----
    api: The websocket/rest API to run.
    app: The Quix application.
    topic: The Kafka topic.

    """
    async with api:
        with app.get_producer() as producer:
            while not api.is_done():

                # Monitor performance
                start_time = time.time()
                trades = await api.run()
                latency = time.time() - start_time
                monitoring.observe_request(exchange=api.name, metric=latency)
                monitoring.increment_request_count(exchange=api.name)

                # Send trades to redpanda
                for trade in trades:
                    #logger.info(f"Sending {trade} to redpanda")
                    message = topic.serialize(
                        trade.product_id, value=trade.model_dump()
                    )
                    producer.produce(
                        topic.name, value=message.value, key=message.key
                    )


if __name__ == "__main__":
    logger.info(f"{settings}")
    logger.info("Configuration parameters logged.")
    asyncio.run(produce_trades())
