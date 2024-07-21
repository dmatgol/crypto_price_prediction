import json

from websocket import WebSocketConnectionClosedException, create_connection


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
        self._ws = self._connect()
        self._subscribe_to_trades()
        self._skip_initial_messages()

    def _connect(self):
        """Create a websocket connection to the Kraken API."""
        try:
            ws = create_connection(self.URL)
            print("Connection established.")
            return ws
        except WebSocketConnectionClosedException as e:
            print(f"Connection error: {e}")
            return None

    def _subscribe_to_trades(self):
        """Subscribe to the product's trade feed."""
        subscribe_message = {
            "method": "subscribe",
            "params": {
                "channel": "trade",
                "symbol": [self.product_id],
                "snapshot": True,
            },
        }
        try:
            self._ws.send(json.dumps(subscribe_message))
            print(f"Subscribed to trades for {self.product_id}.")
        except WebSocketConnectionClosedException as e:
            print(f"Subscription error: {e}")

    def _skip_initial_messages(self) -> None:
        """Skip first two messages from websocket.

        First two messages contain no trade info, just confirmation that
        subscription is sucessful.
        """
        _ = self._ws.recv()
        _ = self._ws.recv()

    def get_trades(self) -> list[dict]:
        """
        Read trades from the Kraken websocket and return a list of dicts.

        Returns:
            list[dict]: A list of dictionaries representing the trades.
        """
        message = self._ws.recv()

        if "heartbeat" in message:
            return []

        message = json.loads(message)
        trades = []

        for trade in message["data"]:
            trades.append(
                {
                    "product_id": self.product_id,
                    "side": trade["side"],
                    "price": trade["price"],
                    "volume": trade["qty"],
                    "timestamp": trade["timestamp"],
                }
            )

        return trades
