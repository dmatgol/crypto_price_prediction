import json

from websocket import create_connection


class KrakenWebsocketTradeAPI:
    """Kraken Websocket API for trade data."""

    URL = "wss://ws.kraken.com/v2"

    def __init__(self, product_id: str) -> None:
        """
        Initialize the KrakenWebsocketTradeAPI with the provided websocket URL.

        Args:
            product_id (str): The product ID to subscribe to.
        """
        self.product_id = product_id
        self._ws = create_connection(self.URL)

        # Subscribe to the product's trade feed
        subscribe_message = {
            "method": "subscribe",
            "params": {
                "channel": "trade",
                "symbol": [self.product_id],
                "snapshot": False,
            },
        }

        self._ws.send(json.dumps(subscribe_message))

    def get_trades(self) -> list[dict]:
        """
        Read trades from the Kraken websocket and return a list of dicts.

        Returns:
            list[dict]: A list of dictionaries representing the trades.
        """
        data = self._ws.recv()
        data = json.loads(data)
        return data
