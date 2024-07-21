from quixstreams import Application

from services.trade_producer.src.api.kraken_api import KrakenWebsocketTradeAPI


def product_trades(kakfka_broker_address: str, kafka_topic: str) -> None:
    """Read trades from Kraken websocket and send them to a Kafka topic.

    Args:
        kakfka_broker_address (str): The address of Kafka broker.
        kafka_topic (str): The name of the Kafka topic.
    """
    app = Application(broker_address=kakfka_broker_address)
    topic = app.topic(name=kafka_topic, value_serializer="json")

    kraken_api = KrakenWebsocketTradeAPI(product_id="ETH/USD")
    # Producer write to kafka - send message to Kafka topic
    with app.get_producer() as producer:

        while True:

            trades: list[dict] = kraken_api.get_trades()
            for trade in trades:

                message = topic.serialize(trade["product_id"], value=trade)

                # Produce a message into the topic
                producer.produce(
                    topic=topic.name, value=message.value, key=message.key
                )


if __name__ == "__main__":
    product_trades(
        kakfka_broker_address="localhost:19092", kafka_topic="trades"
    )
