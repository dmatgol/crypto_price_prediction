from quixstreams import Application


def product_trades(kakfka_broker_address: str, kafka_topic: str) -> None:
    """Read trades from Kraken websocket and send them to a Kafka topic.

    Args:
        kakfka_broker_address (str): The address of Kafka broker.
        kafka_topic (str): The name of the Kafka topic.
    """
    app = Application(broker_address=kakfka_broker_address)

    topic = app.topic(name=kafka_topic, value_serializer="json")

    event = {
        "id": "1234",
        "price": 123.45,
        "size": 1.23,
        "side": "buy",
        "product_id": "BTC-USD",
    }

    # Producer write to kafka - send message to Kafka topic
    with app.get_producer() as producer:

        while True:
            message = topic.serialize(event["id"], value=event)

            # Produce a message into the topic
            producer.produce(
                topic=topic.name, value=message.value, key=message.key
            )

            from time import sleep

            sleep(1)


if __name__ == "__main__":
    product_trades(
        kakfka_broker_address="localhost:19092", kafka_topic="trades"
    )
