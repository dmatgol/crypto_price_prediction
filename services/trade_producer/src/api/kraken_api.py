import json

from api.base import BaseExchangeWebSocket
from utils.config import logger
from websocket import WebSocketConnectionClosedException


class KrakenWebsocketTradeAPI(BaseExchangeWebSocket):
    """Kraken Websocket API for trade data."""

    URL = "wss://ws.kraken.com/v2"

    def __init__(self, product_ids: list[str], channels: list[str]) -> None:
        """Initialize the KrakenWebsocketAPI with the provided websocket URL.

        Args:
        ----
        product_ids: The product ID to subscribe to.
        channels: The list of channels to subscribe to.

        """
        super().__init__(self.URL, product_ids, channels)

    def _subscribe_to_trades(self):
        """Subscribe to the product's trade feed."""
        subscribe_message = {
            "method": "subscribe",
            "params": {
                "channel": "trade",
                "symbol": self.product_ids,
                "snapshot": True,
            },
        }
        try:
            self._ws.send(json.dumps(subscribe_message))
            logger.info(f"Subscribed to trades for {self.product_ids}.")
        except WebSocketConnectionClosedException as e:
            logger.error(f"Subscription error: {e}")

    def _skip_initial_messages(self) -> None:
        """Skip first two messages of each coin pair from websocket.

        First two messages contain no trade info, just confirmation that
        subscription is sucessful.
        """
        for _ in range(len(self.product_ids)):
            _ = self._ws.recv()
            _ = self._ws.recv()

    def get_trades(self) -> list[dict]:
        """Read trades from the Kraken websocket and return a list of dicts.

        Returns        -------
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
                    "product_id": trade["symbol"],
                    "side": trade["side"],
                    "price": trade["price"],
                    "volume": trade["qty"],
                    "timestamp": trade["timestamp"],
                }
            )

        return trades
