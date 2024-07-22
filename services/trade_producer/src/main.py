from api.kraken_api import KrakenWebsocketTradeAPI
from quixstreams import Application
from utils.config import config, logger


def produce_trades(
    kakfka_broker_address: str, kafka_topic: str, product_id: str
) -> None:
    """Read trades from Kraken websocket and send them to a Kafka topic.

    Args:
    ----
    kakfka_broker_address (str): The address of Kafka broker.
    kafka_topic (str): The name of the Kafka topic.
    product_id (str): The product ID to subscribe to.

    """
    app = Application(broker_address=kakfka_broker_address)
    topic = app.topic(name=kafka_topic, value_serializer="json")

    kraken_api = KrakenWebsocketTradeAPI(product_id=product_id)
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
    produce_trades(
        kakfka_broker_address=config["kafka"]["kakfka_broker_address"],
        kafka_topic=config["kafka"]["kafka_topic"],
        product_id=config["instrument"]["product_id"],
    )
